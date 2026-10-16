#!/usr/bin/env python3
"""
Batch runner: generate N episodes of any format in parallel.

Example:
    python batch.py --format poker --count 10 --workers 4
    python batch.py --format all   --count 30 --workers 4
"""

import argparse
import multiprocessing
import os
import random
import sys

sys.path.insert(0, os.path.dirname(__file__))

from src.engine import Scene, VideoConfig, run_pipeline
from src.video1_would_you_call import make_video as make_poker
from src.video2_ai_said_what  import make_video as make_quotes
from src.video3_60s_showdown  import make_video as make_showdown


def _run_one(args):
    """Worker function for pool.map."""
    fmt, seed, output_dir, engine = args
    try:
        path = f"{output_dir}/{fmt}_{seed:04d}.mp4"
        # For now, each format produces one canonical video per call.
        # A full production system would template-fill from game data.
        if fmt == "poker":
            make_poker(output_dir=output_dir, engine=engine)
        elif fmt == "quotes":
            make_quotes(output_dir=output_dir, engine=engine)
        elif fmt == "showdown":
            make_showdown(output_dir=output_dir, engine=engine)
        return {"status": "ok", "format": fmt, "seed": seed}
    except Exception as exc:
        return {"status": "error", "format": fmt, "seed": seed, "error": str(exc)}


def main():
    parser = argparse.ArgumentParser(description="Batch video generation")
    parser.add_argument("--format", choices=["poker", "quotes", "showdown", "all"],
                        default="all")
    parser.add_argument("--count", type=int, default=3,
                        help="Number of videos to generate")
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--engine", choices=["auto", "edge", "flite"],
                        default="auto")
    parser.add_argument("--output", default="output/batch")
    args = parser.parse_args()

    os.makedirs(args.output, exist_ok=True)

    formats = (["poker", "quotes", "showdown"] if args.format == "all"
               else [args.format])

    jobs = []
    for i in range(args.count):
        fmt = formats[i % len(formats)]
        jobs.append((fmt, i, args.output, args.engine))

    print(f"Generating {len(jobs)} videos with {args.workers} workers...")

    with multiprocessing.Pool(args.workers) as pool:
        results = pool.map(_run_one, jobs)

    ok = [r for r in results if r["status"] == "ok"]
    fail = [r for r in results if r["status"] == "error"]
    print(f"\nBatch complete: {len(ok)} ok, {len(fail)} failed")
    for r in fail:
        print(f"  FAIL: {r['format']} seed={r['seed']}: {r['error']}")


if __name__ == "__main__":
    main()
