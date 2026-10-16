# GGhuman.ai Instagram Video Automation -- Take-Home Submission

## 1. Overview

An automated pipeline that generates Instagram Reels for @gghumanai in a **doodle-art style** matching the existing page aesthetic -- hand-drawn wobbly lines, green-headed human character, AI robot characters with model-specific branding, cream background, word-by-word captions synced to voiceover, and the GGhuman watermark.

**Three video formats produced:**

| # | Format               | Concept                                                     | Duration |
|---|----------------------|-------------------------------------------------------------|----------|
| 1 | "Would You Call?"    | Interactive poker decision reel -- AI bluffs, viewer decides | ~20s     |
| 2 | "AI Said What?"      | Funny AI quotes from Last Vote (Mafia) games                | ~22s     |
| 3 | "60s Showdown"       | Compressed Settler Rush highlight, human vs DeepSeek         | ~22s     |

All three drive engagement and direct players to gghuman.ai.

---

## 2. Tech Stack

Everything is **free/open-source**, zero cost:

- **Python 3** -- main language
- **Pillow** -- frame-by-frame rendering with programmatic doodle art
- **edge-tts** (primary) -- Microsoft neural voices, free, high quality
- **flite** (fallback) -- offline TTS via ctypes, always works
- **FFmpeg** -- frame + audio assembly into MP4 (H.264/AAC, 720x1280, 30fps)
- **No API keys, no paid services, no GPU required**

### Why programmatic rendering over AI video generation?

1. **Consistency** -- same code = same visual style across 100+ videos. AI generators can't match an existing brand reliably.
2. **Speed** -- ~60 seconds per video on a single CPU core.
3. **Cost** -- $0. No API calls, no credits, no subscriptions.
4. **Control** -- every pixel is deterministic (seeded randomness for wobble). Fix a typo without regenerating the entire video.
5. **Scalability** -- trivially parallelisable. 100 videos in ~25 minutes on 4 cores.

---

## 3. Workflow / Code Architecture

```
gghuman-reels/
  generate.py        -- Generate all 3 sample videos
  batch.py           -- Batch-generate N videos in parallel
  validate.py        -- Post-generation quality checks
  src/
    assets.py        -- Drawing library (characters, cards, board, UI)
    engine.py        -- Video pipeline (TTS -> frames -> ffmpeg assembly)
    video1_*.py      -- "Would You Call?" scene definitions
    video2_*.py      -- "AI Said What?" scene definitions
    video3_*.py      -- "60s Showdown" scene definitions
```

### Pipeline (engine.py)

```
Script (scenes + narration text)
    |
    v
[1] TTS Generation (per-scene)
    |  - edge-tts: async streaming with WordBoundary events
    |  - flite fallback: ctypes with estimated word timing
    |  - Generates WAV per scene, concatenates with ffmpeg
    |
    v
[2] Frame Rendering (720x1280, 30fps)
    |  - Iterates timeline, calls scene draw_func(draw, img, progress)
    |  - progress = 0.0 to 1.0 within each scene
    |  - Overlays: watermark (bottom-left), caption word (bottom)
    |  - Seeded randomness: wobble changes every 3 frames for stability
    |
    v
[3] FFmpeg Assembly
    |  - Combines PNG frames + WAV audio -> MP4
    |  - H.264 video, AAC audio, yuv420p pixel format
    |  - -movflags +faststart for web playback
    |
    v
Output: Instagram-ready MP4 (720x1280, 30fps, ~20-30s)
```

### Creating a new video

Define scenes with narration text and a draw function:

```python
from src.engine import Scene, VideoConfig, run_pipeline
from src.assets import draw_human, draw_robot, draw_poker_table

def my_scene(draw, img, t):
    """t goes from 0.0 to 1.0 as the scene progresses."""
    draw_poker_table(draw, 360, 650, width=550, height=280)
    draw_human(draw, 200, 550, scale=0.75, expression="worried")
    draw_robot(draw, 520, 550, scale=0.75, color="chatgpt", expression="smug")

scenes = [
    Scene(duration=3.0, narration="The AI just went all in.", draw_func=my_scene),
    Scene(duration=2.0, narration="Would you call?", draw_func=another_scene),
]

config = VideoConfig(scenes=scenes, output_path="output/my_video.mp4", seed=42)
run_pipeline(config)
```

### Asset library (assets.py)

- `draw_human(draw, cx, cy, scale, expression)` -- expressions: neutral, surprised, smug, worried
- `draw_robot(draw, cx, cy, scale, color, expression)` -- colours: chatgpt, claude, gemini, generic
- `draw_card(draw, cx, cy, value, suit, scale, face_down)` -- playing cards
- `draw_poker_table()`, `draw_chip_stack()`, `draw_speech_bubble()`, `draw_label()`, `draw_banner()`
- `draw_mini_board()`, `draw_hex()` -- Catan-style board elements
- `draw_watermark()`, `draw_caption()` -- overlays
- Primitives: `wobbly_line()`, `wobbly_rect()`, `wobbly_ellipse()`

---

## 4. Quality Checks

### Automated (validate.py):

```bash
python validate.py output/*.mp4
```

Checks per video:
1. **Resolution** -- must be 720x1280
2. **Codec** -- H.264 video, AAC audio
3. **Duration** -- 5-90 seconds
4. **File size** -- under 250 MB
5. **Streams** -- both video and audio present

### Manual spot-checks (recommended for first run of new format):

- Watch end-to-end
- Verify captions sync with audio
- Check watermark visibility
- Confirm CTA/URL is readable

### Failure matrix:

| Issue               | Detection            | Action                                |
|---------------------|----------------------|---------------------------------------|
| TTS service down    | Exception in engine  | Fall back to flite (offline)          |
| Blank frames        | Frame sampling       | Check draw function + scene timeline  |
| Audio missing       | validate.py          | Re-run TTS step                       |
| Caption desync      | Manual review        | Regenerate TTS timestamps             |
| Duration wrong      | validate.py          | Adjust scene durations or narration   |
| File too large      | validate.py          | Increase CRF or reduce duration       |
| FFmpeg failure      | Non-zero exit code   | Retry with safer preset               |

---

## 5. Failure Handling

### Pipeline recovery chain:

```
edge-tts fails -> flite fallback -> if both fail -> silent video + captions only
Frame render error -> catch per-frame, skip, FFmpeg interpolates
FFmpeg fails -> retry with ultrafast preset + higher CRF
Full pipeline fails -> log error, move to next video in batch
```

### Specific failure modes:

1. **TTS unavailable**: edge-tts needs internet. Pipeline auto-falls back to flite (offline, lower quality but always works).

2. **Font not found**: `get_font()` cascades through multiple system font paths and falls back to Pillow's built-in font.

3. **Disk space** (batch of 100 = ~100GB temp frames): Pipeline uses `tempfile.mkdtemp()` and cleans up in a `finally` block. Frames are deleted after each video.

4. **Memory**: Each frame is ~3.6 MB. Frames are written to disk immediately, never held in memory.

---

## 6. Scaling to 100 Videos

### Content variety strategy:

| Format           | What varies per episode             | Source                              |
|------------------|-------------------------------------|-------------------------------------|
| "Would You Call?"| Board, hole cards, AI model, outcome| Random hand generator / game logs   |
| "AI Said What?"  | Quotes, model, game, punchline      | Game transcripts / LLM scenarios    |
| "60s Showdown"   | Game type, AI, scores, winner       | Game replays / synthetic summaries  |

### Batch runner:

```bash
python batch.py --format all --count 100 --workers 4
```

### Production timeline for 100 videos:

| Step                         | Time       | Notes                            |
|------------------------------|------------|----------------------------------|
| Generate 100 configs         | ~5 seconds | Template filling, no API calls   |
| TTS for 100 videos           | ~10 min    | edge-tts async; flite is instant |
| Render frames (4 workers)    | ~25 min    | ~60s per video, 4x parallel      |
| FFmpeg assembly              | ~5 min     | Fast with pre-rendered frames    |
| Validation                   | ~2 min     | Automated checks                 |
| **Total**                    | **~45 min**| 4-core machine, zero cost        |

### Production upgrades (when budget allows):

1. **Real game data**: pull actual game logs from gghuman.ai API
2. **A/B testing**: generate variants, track engagement, iterate
3. **Scheduled posting**: cron -> generate -> validate -> upload via Instagram Graph API
4. **Thumbnail extraction**: auto-extract visually striking frame as cover

---

## 7. Running the Code

### Prerequisites:

```bash
pip install Pillow edge-tts       # edge-tts for production TTS
apt install libflite1              # flite for offline fallback (optional)
# ffmpeg must be in PATH
```

### Generate all 3 sample videos:

```bash
cd gghuman-reels
python generate.py
```

### Output:

```
output/video1_would_you_call.mp4   -- 720x1280, ~20s
output/video2_ai_said_what.mp4     -- 720x1280, ~22s
output/video3_60s_showdown.mp4     -- 720x1280, ~22s
```

---

## 8. Why This Approach Works

The key insight: **treat video creation like code generation, not art generation.**

- AI image generators are creative but **inconsistent** -- can't guarantee brand style across 100 videos
- Programmatic rendering is **predictable and reliable** -- same code = same style, every time
- The "AI" part goes into **content selection** (which moments are interesting) and **narration**, not visual generation
- Hand-drawn doodle style is **forgiving** -- wobbly lines look intentional, not broken

This matches how the existing @gghumanai page already works, and extends it with three new content formats that can run indefinitely.
