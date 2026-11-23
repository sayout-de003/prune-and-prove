#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import analyze_impact, generate_graph, health_check, map_project


COMMANDS = {
    "health": health_check.main,
    "map": map_project.main,
    "graph": generate_graph.main,
    "impact": analyze_impact.main,
}


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or args[0] in {"-h", "--help"} or args[0] not in COMMANDS:
        print(
            "Usage: analyze.py <command> [args...]\n"
            "Commands:\n"
            "  health                         Verify toolkit configuration and parser readiness\n"
            "  map <repo> [-o file] [--json]  Inventory languages, frameworks, and entrypoints\n"
            "  graph <repo> [-o file] [--mermaid file] [--html file]\n"
            "                                 Build, validate, and export 3D interactive knowledge graph\n"
            "  impact <repo> <target> [--depth N] [--json]\n"
            "                                 Compute upstream/downstream blast radius and covering tests",
            file=sys.stderr,
        )
        return 0 if args and args[0] in {"-h", "--help"} else 2

    cmd, rest = args[0], args[1:]
    return COMMANDS[cmd](rest)


if __name__ == "__main__":
    raise SystemExit(main())
