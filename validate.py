#!/usr/bin/env python3
"""
Post-generation quality validator.

Usage:
    python validate.py output/*.mp4
"""

import json
import os
import subprocess
import sys


def ffprobe_info(path: str) -> dict:
    """Extract video metadata via ffprobe."""
    cmd = [
        "ffprobe", "-v", "quiet",
        "-print_format", "json",
        "-show_format", "-show_streams",
        path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return json.loads(result.stdout) if result.returncode == 0 else {}


def validate(path: str) -> list[str]:
    """Validate a single video file. Returns list of issues (empty = pass)."""
    issues = []

    if not os.path.exists(path):
        return [f"File not found: {path}"]

    size_mb = os.path.getsize(path) / 1_000_000
    if size_mb > 250:
        issues.append(f"File too large: {size_mb:.1f} MB (max 250 MB)")

    info = ffprobe_info(path)
    if not info:
        return [f"ffprobe failed on {path}"]

    # Video stream checks
    video_streams = [s for s in info.get("streams", [])
                     if s.get("codec_type") == "video"]
    audio_streams = [s for s in info.get("streams", [])
                     if s.get("codec_type") == "audio"]

    if not video_streams:
        issues.append("No video stream found")
    else:
        vs = video_streams[0]
        w = int(vs.get("width", 0))
        h = int(vs.get("height", 0))
        if (w, h) != (720, 1280):
            issues.append(f"Resolution {w}x{h}, expected 720x1280")
        if vs.get("codec_name") != "h264":
            issues.append(f"Video codec: {vs.get('codec_name')}, expected h264")

    if not audio_streams:
        issues.append("No audio stream found")
    else:
        if audio_streams[0].get("codec_name") not in ("aac", "mp3"):
            issues.append(f"Audio codec: {audio_streams[0].get('codec_name')}")

    # Duration
    duration = float(info.get("format", {}).get("duration", 0))
    if duration < 5:
        issues.append(f"Too short: {duration:.1f}s")
    elif duration > 90:
        issues.append(f"Too long: {duration:.1f}s")

    return issues


def main():
    if len(sys.argv) < 2:
        print("Usage: python validate.py <video1.mp4> [video2.mp4 ...]")
        sys.exit(1)

    all_pass = True
    for path in sys.argv[1:]:
        issues = validate(path)
        if issues:
            print(f"FAIL  {path}")
            for issue in issues:
                print(f"      - {issue}")
            all_pass = False
        else:
            info = ffprobe_info(path)
            dur = float(info.get("format", {}).get("duration", 0))
            size = os.path.getsize(path) / 1_000_000
            print(f"PASS  {path}  ({dur:.1f}s, {size:.1f} MB)")

    sys.exit(0 if all_pass else 1)


if __name__ == "__main__":
    main()
