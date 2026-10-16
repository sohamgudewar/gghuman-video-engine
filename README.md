# GGhuman.ai Instagram Reels Generator

Automated pipeline for generating Instagram Reels in **tactile Claymation stop-motion style** for [@gghumanai](https://instagram.com/gghumanai).

## Quick Start

```bash
pip install -r requirements.txt   # Pillow + edge-tts
# ffmpeg must be in PATH

python generate.py                # generates all 3 sample videos
python generate.py --engine edge  # force high-quality neural TTS
python generate.py --engine flite # force offline TTS (no internet needed)
```

Output lands in `output/`.

## Project Structure

```
gghuman-reels/
  generate.py        # Generate all 3 sample videos
  batch.py           # Batch-generate N videos in parallel
  validate.py        # Post-generation quality checks
  requirements.txt   # Python dependencies
  src/
    assets.py        # Claymation drawing library (characters, cards, board, UI)
    engine.py        # Video pipeline (TTS -> frames -> ffmpeg assembly)
    video1_*.py      # "Would You Call?" poker reel
    video2_*.py      # "AI Said What?" negotiation quotes reel
    video3_*.py      # "60s Showdown" game highlight reel
  output/            # Generated videos
```

## TTS Engines

| Engine   | Quality     | Requires    | Notes                         |
|----------|-------------|-------------|-------------------------------|
| edge-tts | Neural      | Internet    | Microsoft voices, free, async |
| flite    | Robotic     | libflite.so | Always works offline          |

Default (`--engine auto`) tries edge-tts first, falls back to flite.

## Batch Generation

```bash
python batch.py --format all --count 30 --workers 4
```

## Validation

```bash
python validate.py output/*.mp4
```

Checks: resolution (720x1280), codec (H.264/AAC), duration (5-90s), file size (<250MB).
