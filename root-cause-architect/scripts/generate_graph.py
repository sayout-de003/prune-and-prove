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
from engine.graph.graph_validator import GraphValidator


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build and validate the Architecture Knowledge Graph.")
    parser.add_argument("repo", help="Path to the target repository")
    parser.add_argument("--output", "-o", help="Write dependency-graph JSON to this path")
    parser.add_argument("--mermaid", help="Write Mermaid flowchart to this path")
    parser.add_argument("--include-external", action="store_true", help="Include external packages in Mermaid output")
    args = parser.parse_args(argv)

    graph, _ = GraphBuilder().build_from_path(args.repo)
    validation = GraphValidator().validate(graph)

    if args.output:
        GraphExporter.write_json(graph, args.output)
    if args.mermaid:
        mmd_path = Path(args.mermaid)
        mmd_path.parent.mkdir(parents=True, exist_ok=True)
        mmd_path.write_text(
            GraphExporter.to_mermaid(graph, include_external=args.include_external),
            encoding="utf-8",
        )

    summary = {
        "root": graph.root,
        "validation": validation.to_dict(),
        "output_json": args.output,
        "output_mermaid": args.mermaid,
    }
    print(json.dumps(summary, indent=2))
    return 0 if validation.valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
