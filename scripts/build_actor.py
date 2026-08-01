#!/usr/bin/env python3
"""Vendor the shared `fedstack` core into each actor, then optionally deploy.

Apify pushes a single directory, and there is no private package registry in a
$0 budget. So the shared core lives in one place in git and is copied into each
actor immediately before build. The copies are gitignored — `src/fedstack` is
always the single source of truth.

Usage:
    python scripts/build_actor.py                 # vendor into every actor
    python scripts/build_actor.py --push          # vendor, then `apify push` each
    python scripts/build_actor.py --actor grants-gov-scraper --push
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CORE = ROOT / "src" / "fedstack"
ACTORS_DIR = ROOT / "actors"


def discover_actors(only: str | None) -> list[Path]:
    if not ACTORS_DIR.is_dir():
        sys.exit(f"No actors directory at {ACTORS_DIR}")
    actors = sorted(p for p in ACTORS_DIR.iterdir() if (p / ".actor").is_dir())
    if only:
        actors = [p for p in actors if p.name == only]
        if not actors:
            sys.exit(f"No actor named {only!r} in {ACTORS_DIR}")
    return actors


def vendor(actor: Path) -> None:
    target = actor / "src" / "fedstack"
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(CORE, target, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    print(f"  vendored core -> {target.relative_to(ROOT)}")


def push(actor: Path) -> None:
    # npx keeps apify-cli off the machine permanently and off the budget entirely.
    cmd = ["npx", "-y", "apify-cli@latest", "push", "--no-prompt"]
    print(f"  $ {' '.join(cmd)}  (cwd={actor.name})")
    result = subprocess.run(cmd, cwd=actor, shell=sys.platform == "win32")
    if result.returncode != 0:
        sys.exit(f"apify push failed for {actor.name} (exit {result.returncode})")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--actor", help="Only build this one actor")
    parser.add_argument("--push", action="store_true", help="Run `apify push` after")
    args = parser.parse_args()

    if not CORE.is_dir():
        sys.exit(f"Shared core not found at {CORE}")

    for actor in discover_actors(args.actor):
        print(f"{actor.name}:")
        vendor(actor)
        if args.push:
            push(actor)

    print("Done.")


if __name__ == "__main__":
    main()
