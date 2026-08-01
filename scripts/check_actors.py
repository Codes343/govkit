#!/usr/bin/env python3
"""Validate every actor directory before it can reach the Store.

A malformed input schema or a mismatched actor name fails at `apify push` time,
which in an unattended pipeline means a silent non-deploy. Catching it in CI is
the difference between "the fix shipped" and "the fix sat in git for a week".
"""

from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ACTORS_DIR = ROOT / "actors"

REQUIRED_FILES = (
    ".actor/actor.json",
    ".actor/input_schema.json",
    ".actor/dataset_schema.json",
    "Dockerfile",
    "requirements.txt",
    "README.md",
    "src/main.py",
    "src/__main__.py",
)

VALID_EDITORS = {
    "textfield",
    "textarea",
    "stringList",
    "select",
    "datepicker",
    "json",
    "hidden",
    "checkbox",
    "number",
    "keyValue",
}


def _load_json(path: Path, errors: list[str]) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"{path.relative_to(ROOT)}: {exc}")
        return None


def check_actor(actor: Path) -> list[str]:
    errors: list[str] = []

    for rel in REQUIRED_FILES:
        if not (actor / rel).is_file():
            errors.append(f"{actor.name}: missing required file {rel}")
    if errors:
        return errors

    manifest = _load_json(actor / ".actor" / "actor.json", errors)
    if manifest:
        if manifest.get("name") != actor.name:
            errors.append(
                f"{actor.name}: actor.json name is {manifest.get('name')!r}, "
                "which must equal the directory name"
            )
        for key in ("title", "description", "version", "dockerfile", "inputSchema"):
            if not manifest.get(key):
                errors.append(f"{actor.name}: actor.json is missing {key!r}")
        if "input" in manifest:
            errors.append(
                f"{actor.name}: actor.json uses the deprecated 'input' key; "
                "rename it to 'inputSchema'"
            )
        title = manifest.get("title") or ""
        # Apify Store truncates long titles in search results.
        if len(title) > 90:
            errors.append(f"{actor.name}: title is {len(title)} chars (max 90)")

    schema = _load_json(actor / ".actor" / "input_schema.json", errors)
    if schema:
        if schema.get("schemaVersion") != 1:
            errors.append(f"{actor.name}: input_schema.json needs schemaVersion 1")
        props = schema.get("properties") or {}
        if not props:
            errors.append(f"{actor.name}: input schema declares no properties")
        for name, prop in props.items():
            if not prop.get("title"):
                errors.append(f"{actor.name}: input {name!r} has no title")
            if not prop.get("description"):
                # Descriptions are how this business does customer support.
                errors.append(f"{actor.name}: input {name!r} has no description")
            editor = prop.get("editor")
            if editor and editor not in VALID_EDITORS:
                errors.append(
                    f"{actor.name}: input {name!r} has unknown editor {editor!r}"
                )
            if prop.get("type") == "array" and "items" not in prop:
                errors.append(f"{actor.name}: array input {name!r} has no items schema")

    # Parse rather than import: the actor entrypoint imports `apify`, which we
    # do not want as a CI dependency just to check the file is well-formed.
    main_py = actor / "src" / "main.py"
    try:
        tree = ast.parse(main_py.read_text(encoding="utf-8"))
    except SyntaxError as exc:
        errors.append(f"{actor.name}: src/main.py does not parse: {exc}")
    else:
        has_main = any(
            isinstance(node, ast.AsyncFunctionDef) and node.name == "main"
            for node in tree.body
        )
        if not has_main:
            errors.append(f"{actor.name}: src/main.py defines no `async def main()`")

    readme = (actor / "README.md").read_text(encoding="utf-8")
    if len(readme) < 800:
        errors.append(
            f"{actor.name}: README is {len(readme)} chars. It is the Store listing "
            "and the primary SEO surface; write a real one."
        )
    if "## Pricing" not in readme:
        errors.append(f"{actor.name}: README has no Pricing section")

    return errors


def main() -> int:
    if not ACTORS_DIR.is_dir():
        print(f"No actors directory at {ACTORS_DIR}", file=sys.stderr)
        return 1

    actors = sorted(p for p in ACTORS_DIR.iterdir() if (p / ".actor").is_dir())
    if not actors:
        print("No actors found.", file=sys.stderr)
        return 1

    all_errors: list[str] = []
    for actor in actors:
        errors = check_actor(actor)
        print(f"{'FAIL' if errors else 'PASS'}  {actor.name}")
        all_errors.extend(errors)

    if all_errors:
        print("\nProblems found:", file=sys.stderr)
        for error in all_errors:
            print(f"  - {error}", file=sys.stderr)
        return 1

    print(f"\n{len(actors)} actor(s) valid.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
