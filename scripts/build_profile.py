#!/usr/bin/env python3
"""Regenerate the profile README's images and projects table from GitHub data.

GITHUB_TOKEN=... python3 scripts/build_profile.py
python3 scripts/build_profile.py --raw pages.json   # offline, from saved GraphQL payloads
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from readmegen import cards, config, github, readme

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
README = ROOT / "README.md"


def build(stats: github.Stats, now: datetime, readme_text: str) -> dict[Path, str]:
    """Every generated file and its new content."""
    table = readme.projects_table(stats.featured())
    return {
        ASSETS / "hero.svg": cards.hero(stats, now),
        ASSETS / "stats.svg": cards.stats_card(stats),
        ASSETS / "languages.svg": cards.languages_card(stats),
        ASSETS / "activity.svg": cards.activity_card(stats),
        README: readme.replace_block(readme_text, table),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--raw", type=Path, help="JSON list of GraphQL `user` payloads")
    args = parser.parse_args(argv)

    if args.raw:
        pages = json.loads(args.raw.read_text(encoding="utf-8"))
    else:
        token = os.environ.get("GITHUB_TOKEN")
        if not token:
            parser.error("GITHUB_TOKEN is not set (or pass --raw FILE for an offline build)")
        pages = github.fetch_pages(config.LOGIN, token)

    stats = github.summarize(pages)
    outputs = build(stats, datetime.now(timezone.utc), README.read_text(encoding="utf-8"))
    ASSETS.mkdir(exist_ok=True)
    for path, content in outputs.items():
        path.write_text(content, encoding="utf-8")
        print(f"wrote {path.relative_to(ROOT)} ({len(content.encode()):,} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
