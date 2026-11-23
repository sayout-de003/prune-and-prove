#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.graph.graph_builder import GraphBuilder
from engine.graph.graph_exporter import GraphExporter


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Analyze blast-radius impact for a file or symbol.")
    parser.add_argument("repo", help="Path to the target repository")
    parser.add_argument("target", help="Relative file path, symbol name, or graph node ID")
    parser.add_argument("--depth", type=int, default=3, help="Max traversal depth (default: 3)")
    parser.add_argument("--json", action="store_true", dest="as_json", help="Emit JSON instead of Markdown")
    args = parser.parse_args(argv)

    graph, _ = GraphBuilder().build_from_path(args.repo)
    impact = graph.blast_radius(args.target, max_depth=args.depth)

    if args.as_json:
        print(json.dumps(impact, indent=2))
    else:
        print(GraphExporter.format_impact_markdown(impact), end="")
    return 0 if impact["matched_nodes"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
