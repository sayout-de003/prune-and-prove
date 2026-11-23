#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.repository.manifest_builder import ManifestBuilder


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Map a repository's languages, manifests, frameworks, and entrypoints.")
    parser.add_argument("repo", help="Path to the target repository")
    parser.add_argument("--output", "-o", help="Optional output file path")
    parser.add_argument("--json", action="store_true", dest="as_json", help="Emit JSON instead of Markdown")
    args = parser.parse_args(argv)

    manifest, _ = ManifestBuilder().build(args.repo)
    rendered = (
        json.dumps(manifest.to_dict(), indent=2) + "\n"
        if args.as_json
        else manifest.to_markdown()
    )

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
