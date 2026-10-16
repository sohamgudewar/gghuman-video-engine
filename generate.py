#!/usr/bin/env python3
"""
Generate all 3 sample GGhuman.ai Instagram reels.

Usage:
    python generate.py                  # auto TTS (edge-tts -> flite fallback)
    python generate.py --engine edge    # force edge-tts only
    python generate.py --engine flite   # force flite only (offline)
"""

import argparse
import os
import sys

# Ensure project root is importable
sys.path.insert(0, os.path.dirname(__file__))

from src.video1_would_you_call import make_video as make_v1
from src.video2_ai_said_what  import make_video as make_v2
from src.video3_60s_showdown  import make_video as make_v3


def main():
    parser = argparse.ArgumentParser(description="Generate GGhuman Instagram reels")
    parser.add_argument("--engine", choices=["auto", "edge", "flite"],
                        default="auto",
                        help="TTS engine: auto (try edge, fall back to flite), "
                             "edge (online neural), flite (offline robotic)")
    parser.add_argument("--output", default="output",
                        help="Output directory (default: output/)")
    args = parser.parse_args()

    os.makedirs(args.output, exist_ok=True)

    videos = [
        ("Video 1: Would You Call?",  make_v1),
        ("Video 2: AI Said What?",    make_v2),
        ("Video 3: 60s Showdown",     make_v3),
    ]

    results = {"ok": [], "fail": []}

    for name, fn in videos:
        try:
            fn(output_dir=args.output, engine=args.engine)
            results["ok"].append(name)
        except Exception as exc:
            print(f"\nFAILED: {name}: {exc}")
            results["fail"].append(name)

    print(f"\n{'=' * 60}")
    print(f"Done.  {len(results['ok'])} succeeded, {len(results['fail'])} failed.")
    for v in results["ok"]:
        print(f"  OK   {v}")
    for v in results["fail"]:
        print(f"  FAIL {v}")


if __name__ == "__main__":
    main()
