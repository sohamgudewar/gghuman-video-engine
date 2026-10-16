"""
GGhuman Video Engine
Generates Instagram reels from scene descriptions.

Pipeline: Script -> TTS -> Frame rendering -> Caption sync -> FFmpeg assembly

TTS priority:
  1. edge-tts  (Microsoft neural voices, free, needs internet)
  2. flite     (offline via ctypes, robotic but always works)
"""

import asyncio
import ctypes
import math
import os
import random
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, List, Optional

from PIL import Image, ImageDraw

from .assets import (
    CREAM_BG, create_frame, draw_caption, draw_watermark,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
WIDTH  = 720
HEIGHT = 1280
FPS    = 30


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------
@dataclass
class Scene:
    """A single scene in the video."""
    duration: float           # seconds (estimate; adjusted to actual TTS)
    narration: str = ""       # spoken text
    draw_func: Optional[Callable] = None  # func(draw, img, progress)
    transition: str = "cut"   # "cut" or "fade"


@dataclass
class VideoConfig:
    """Full video configuration."""
    scenes: List[Scene] = field(default_factory=list)
    output_path: str = "output.mp4"
    seed: int = 42


# ---------------------------------------------------------------------------
# TTS: edge-tts (primary, high-quality neural voices)
# ---------------------------------------------------------------------------
async def _edge_tts_generate(text: str, output_wav: str,
                              voice: str = "en-US-GuyNeural"):
    """Generate speech with edge-tts. Returns (word_boundaries, duration)."""
    import edge_tts

    mp3_path = output_wav.replace(".wav", ".mp3")
    try:
        communicate = edge_tts.Communicate(text, voice, boundary="WordBoundary")
    except TypeError:
        communicate = edge_tts.Communicate(text, voice)
    words = []

    with open(mp3_path, "wb") as f:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                words.append({
                    "text": chunk["text"],
                    "offset_s": chunk["offset"] / 1e7,
                    "duration_s": chunk["duration"] / 1e7,
                })

    # Convert mp3 -> wav for consistent downstream handling
    subprocess.run([
        "ffmpeg", "-y", "-i", mp3_path, "-ar", "16000", "-ac", "1",
        output_wav
    ], capture_output=True)
    os.remove(mp3_path)

    # Get actual duration
    probe = subprocess.run(
        ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
         "-of", "csv=p=0", output_wav],
        capture_output=True, text=True
    )
    duration = float(probe.stdout.strip()) if probe.stdout.strip() else 0.0

    return words, duration


def generate_tts_edge(text: str, output_wav: str,
                      voice: str = "en-US-GuyNeural"):
    """Synchronous wrapper for edge-tts."""
    return asyncio.run(_edge_tts_generate(text, output_wav, voice))


# ---------------------------------------------------------------------------
# TTS: flite (fallback, offline)
# ---------------------------------------------------------------------------
def generate_tts_flite(text: str, output_wav: str, voice: str = "rms"):
    """Generate speech via flite ctypes. Returns (word_boundaries, duration)."""
    flite = ctypes.cdll.LoadLibrary("libflite.so.1")
    ctypes.cdll.LoadLibrary("libflite_usenglish.so.1")
    ctypes.cdll.LoadLibrary("libflite_cmulex.so.1")
    voice_lib = ctypes.cdll.LoadLibrary(f"libflite_cmu_us_{voice}.so.1")

    flite.flite_init()

    register_fn = getattr(voice_lib, f"register_cmu_us_{voice}")
    register_fn.restype = ctypes.c_void_p
    voice_ptr = register_fn(ctypes.c_char_p(b""))

    flite.flite_text_to_speech.argtypes = [
        ctypes.c_char_p, ctypes.c_void_p, ctypes.c_char_p
    ]
    flite.flite_text_to_speech.restype = ctypes.c_float

    duration = flite.flite_text_to_speech(
        text.encode("utf-8"), voice_ptr, output_wav.encode("utf-8")
    )

    # Estimate word boundaries (flite ctypes has no timing API)
    words_list = text.split()
    words = []
    if words_list and duration > 0:
        avg = duration / len(words_list)
        offset = 0.05
        for w in words_list:
            word_dur = avg * (0.7 + 0.6 * len(w) / 5)
            word_dur = max(0.15, min(word_dur, avg * 1.5))
            words.append({
                "text": w,
                "offset_s": offset,
                "duration_s": word_dur * 0.8,
            })
            offset += word_dur
        if offset > 0:
            scale = (duration - 0.1) / offset
            for wd in words:
                wd["offset_s"] *= scale
                wd["duration_s"] *= scale

    return words, duration


# ---------------------------------------------------------------------------
# TTS dispatcher (tries edge-tts, falls back to flite)
# ---------------------------------------------------------------------------
def generate_tts(text: str, output_wav: str, engine: str = "auto",
                 voice_edge: str = "en-US-GuyNeural",
                 voice_flite: str = "rms"):
    """Generate TTS with automatic fallback.

    engine: "auto" | "edge" | "flite"
    """
    if engine in ("auto", "edge"):
        try:
            return generate_tts_edge(text, output_wav, voice_edge)
        except Exception as exc:
            if engine == "edge":
                raise
            print(f"  [TTS] edge-tts failed ({exc}), falling back to flite")

    return generate_tts_flite(text, output_wav, voice_flite)


# ---------------------------------------------------------------------------
# Per-scene TTS + concatenation
# ---------------------------------------------------------------------------
def generate_tts_per_scene(scenes: List[Scene], work_dir: str,
                           engine: str = "auto"):
    """Generate TTS per scene, concatenate, return audio + word list + durations."""
    scene_wavs = []
    all_words = []
    scene_durations = []
    time_offset = 0.0

    for i, scene in enumerate(scenes):
        wav_path = os.path.join(work_dir, f"scene_{i}.wav")

        if not scene.narration.strip():
            # Silent scene
            dur = scene.duration
            subprocess.run([
                "ffmpeg", "-y", "-f", "lavfi",
                "-i", f"anullsrc=r=16000:cl=mono",
                "-t", str(dur), wav_path
            ], capture_output=True)
            scene_wavs.append(wav_path)
            scene_durations.append(dur)
            time_offset += dur
            continue

        words, duration = generate_tts(scene.narration, wav_path, engine)

        for w in words:
            w["offset_s"] += time_offset

        all_words.extend(words)
        scene_wavs.append(wav_path)
        scene_durations.append(duration)
        time_offset += duration

    # Concatenate
    concat_list = os.path.join(work_dir, "concat.txt")
    with open(concat_list, "w") as f:
        for wav in scene_wavs:
            wav_clean = wav.replace("\\", "/")
            f.write(f"file '{wav_clean}'\n")

    combined = os.path.join(work_dir, "narration.wav")
    res = subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", concat_list, "-c", "copy", combined
    ], capture_output=True, text=True)
    if res.returncode != 0:
        print(f"FFmpeg concat error: {res.stderr[-500:]}")

    return combined, all_words, scene_durations


# ---------------------------------------------------------------------------
# Frame rendering
# ---------------------------------------------------------------------------
def get_current_word(words: List[dict], current_time: float) -> Optional[str]:
    """Look up the word being spoken at *current_time*."""
    for w in words:
        start = w["offset_s"]
        end = start + w["duration_s"]
        if start <= current_time <= end + 0.15:
            return w["text"]
    return None


def render_frames(scenes: List[Scene], words: List[dict], output_dir: str,
                  total_duration: float, seed: int = 42):
    """Render every frame to disk as numbered PNGs."""
    os.makedirs(output_dir, exist_ok=True)
    total_frames = int(total_duration * FPS)

    # Build timeline
    timeline = []
    t = 0.0
    for scene in scenes:
        timeline.append((t, t + scene.duration, scene))
        t += scene.duration

    for idx in range(total_frames):
        current_time = idx / FPS
        # Stop-motion cadence: stepped randomness on twos (15 fps)
        step_idx = idx // 2
        random.seed(seed + step_idx)

        # Active scene
        active = scenes[-1]
        scene_start = 0.0
        for start, end, scene in timeline:
            if start <= current_time < end:
                active = scene
                scene_start = start
                break

        # Stop-motion stepped progress
        raw_progress = ((current_time - scene_start) / active.duration
                        if active.duration > 0 else 0)
        steps_total = max(1, int(active.duration * 15))
        progress = min(1.0, max(0.0, round(raw_progress * steps_total) / steps_total))

        img = create_frame(WIDTH, HEIGHT)
        draw = ImageDraw.Draw(img)

        if active.draw_func:
            active.draw_func(draw, img, progress)

        draw_watermark(draw, WIDTH, HEIGHT)

        word = get_current_word(words, current_time)
        if word:
            draw_caption(draw, WIDTH // 2, HEIGHT - 280,
                         word.upper(), scale=1.0)

        img.save(os.path.join(output_dir, f"frame_{idx:05d}.png"),
                 optimize=True)

        if idx % 30 == 0:
            print(f"  Rendered frame {idx}/{total_frames}")

    print(f"  Rendered {total_frames} frames total")
    return total_frames


# ---------------------------------------------------------------------------
# FFmpeg assembly
# ---------------------------------------------------------------------------
def assemble_video(frames_dir: str, audio_path: str, output_path: str,
                   fps: int = FPS):
    """Combine PNG frames + audio into final MP4."""
    cmd = [
        "ffmpeg", "-y",
        "-framerate", str(fps),
        "-i", os.path.join(frames_dir, "frame_%05d.png").replace("\\", "/"),
        "-i", audio_path,
        "-c:v", "libx264", "-preset", "medium", "-crf", "23",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k",
        "-shortest",
        "-movflags", "+faststart",
        output_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"FFmpeg error: {result.stderr[-500:]}")
        raise RuntimeError("FFmpeg failed")

    # Report duration
    probe = subprocess.run(
        ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
         "-of", "csv=p=0", output_path],
        capture_output=True, text=True
    )
    dur = float(probe.stdout.strip()) if probe.stdout.strip() else 0
    print(f"  Video saved: {output_path}  ({dur:.1f}s)")


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------
def generate_video(config: VideoConfig, engine: str = "auto"):
    """Full pipeline: scenes -> TTS -> frames -> video."""
    print(f"\n{'=' * 60}")
    print(f"Generating: {config.output_path}")
    print(f"{'=' * 60}")

    work_dir = tempfile.mkdtemp(prefix="gghuman_")
    frames_dir = os.path.join(work_dir, "frames")

    try:
        # 1. TTS
        print("\n[1/3] Generating TTS...")
        audio_path, words, scene_durations = generate_tts_per_scene(
            config.scenes, work_dir, engine
        )
        print(f"  {len(words)} word boundaries")

        # Update durations to match actual audio
        for i, scene in enumerate(config.scenes):
            if i < len(scene_durations):
                scene.duration = scene_durations[i]

        total = sum(s.duration for s in config.scenes)
        print(f"  Total duration: {total:.1f}s")

        # 2. Frames
        print("\n[2/3] Rendering frames...")
        render_frames(config.scenes, words, frames_dir, total, config.seed)

        # 3. Assemble
        print("\n[3/3] Assembling video...")
        os.makedirs(os.path.dirname(os.path.abspath(config.output_path)),
                    exist_ok=True)
        assemble_video(frames_dir, audio_path, config.output_path)

        print(f"\nDone -> {config.output_path}")

    finally:
        shutil.rmtree(work_dir, ignore_errors=True)


def run_pipeline(config: VideoConfig, engine: str = "auto"):
    """Entry point. engine: 'auto' | 'edge' | 'flite'."""
    generate_video(config, engine)
