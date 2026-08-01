#!/usr/bin/env python3
"""Vendor the shared `govkit` core into each actor, then optionally deploy.

Apify pushes a single directory, and there is no private package registry in a
$0 budget. So the shared core lives in one place in git and is copied into each
actor immediately before build. The copies are gitignored — `src/govkit` is
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
CORE = ROOT / "src" / "govkit"
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
    target = actor / "src" / "govkit"
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(CORE, target, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    print(f"  vendored core -> {target.relative_to(ROOT)}")


def push(actor: Path) -> None:
    # npx keeps apify-cli off the machine permanently and off the budget entirely.
    #
    # Pinned to the 1.x line rather than @latest: an unattended deploy pipeline
    # should not silently pick up a new major version of its own tooling.
    #
    # --force: without it the CLI refuses when local files look older than what
    #   is already on the platform, which a fresh CI checkout always does
    #   (checkout sets mtime to clone time, not commit time).
    # --wait-for-finish: block on the Docker build so a broken image fails the
    #   workflow here, instead of appearing to deploy and then 404ing for a
    #   customer. Bounded so the job can never hang.
    #
    # There is deliberately no --no-prompt: no such flag exists, and passing an
    # unknown flag makes the CLI exit non-zero. `push` has no interactive
    # prompts, so it is already CI-safe.
    cmd = [
        "npx",
        "-y",
        "apify-cli@1",
        "push",
        "--force",
        "--wait-for-finish=600",
    ]
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
