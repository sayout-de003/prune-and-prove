from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from engine.graph.dependency_graph import DependencyGraph


def _safe_json_for_html(payload: dict[str, Any]) -> str:
    """Serialize JSON safely for embedding inside a <script> tag."""
    raw = json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
    return raw.replace("</", "<\\/").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")


def _module_group(file_path: str | None, kind: str) -> str:
    if kind == "external":
        return "external"
    if not file_path:
        return kind
    parts = [p for p in file_path.replace("\\", "/").split("/") if p]
    if len(parts) >= 2:
        return "/".join(parts[:2])
    return parts[0] if parts else "root"


def build_3d_payload(
    graph: DependencyGraph,
    validation: dict[str, Any] | None = None,
    include_external: bool = False,
    pipeline_depth: int = 8,
    max_pipelines: int = 35,
) -> dict[str, Any]:
    """Build compact, deterministic graph + pipeline payload for the 3D WebGL explorer."""
    included_ids: set[str] = set()
    nodes_out: list[dict[str, Any]] = []

    in_deg: dict[str, int] = {}
    out_deg: dict[str, int] = {}
    for edge in graph.edges:
        out_deg[edge.source] = out_deg.get(edge.source, 0) + 1
        in_deg[edge.target] = in_deg.get(edge.target, 0) + 1

    for nid, node in sorted(graph.nodes.items()):
        if not include_external and node.kind == "external":
            continue
        included_ids.add(nid)
        meta = node.metadata or {}
        nodes_out.append(
            {
                "id": nid,
                "kind": node.kind,
                "label": node.label,
                "file": node.file_path,
                "group": _module_group(node.file_path, node.kind),
                "startLine": meta.get("start_line") or meta.get("line"),
                "endLine": meta.get("end_line"),
                "params": meta.get("parameters", []),
                "decorators": meta.get("decorators", []),
                "inDeg": in_deg.get(nid, 0),
                "outDeg": out_deg.get(nid, 0),
            }
        )

    edges_out: list[dict[str, Any]] = []
    # Aggregate cross-file function calls so File-to-File mode shows exact function links
    file_call_agg: dict[tuple[str, str], list[dict[str, Any]]] = {}

    for edge in sorted(graph.edges, key=lambda e: (e.source, e.relation, e.target)):
        if edge.source not in included_ids or edge.target not in included_ids:
            continue
        src_node = graph.nodes[edge.source]
        tgt_node = graph.nodes[edge.target]
        edges_out.append(
            {
                "source": edge.source,
                "target": edge.target,
                "relation": edge.relation,
                "provenance": edge.provenance,
                "line": edge.metadata.get("line"),
                "rawCallee": edge.metadata.get("raw_callee"),
            }
        )
        if (
            edge.relation == "CALLS"
            and src_node.file_path
            and tgt_node.file_path
            and src_node.file_path != tgt_node.file_path
        ):
            fkey = (f"file:{src_node.file_path}", f"file:{tgt_node.file_path}")
            if fkey[0] in included_ids and fkey[1] in included_ids:
                file_call_agg.setdefault(fkey, []).append(
                    {
                        "caller": edge.source,
                        "callerLabel": src_node.label,
                        "callee": edge.target,
                        "calleeLabel": tgt_node.label,
                        "line": edge.metadata.get("line"),
                        "provenance": edge.provenance,
                    }
                )

    file_call_links = [
        {
            "source": src_f,
            "target": tgt_f,
            "relation": "FILE_CALLS",
            "count": len(calls),
            "calls": calls[:25],
        }
        for (src_f, tgt_f), calls in sorted(file_call_agg.items())
    ]

    pipelines = graph.discover_pipelines(max_pipelines=max_pipelines, max_depth=pipeline_depth)

    kind_counts: dict[str, int] = {}
    for n in nodes_out:
        kind_counts[n["kind"]] = kind_counts.get(n["kind"], 0) + 1

    return {
        "root": Path(graph.root).name or graph.root,
        "rootPath": graph.root,
        "stats": {
            "nodes": len(nodes_out),
            "edges": len(edges_out),
            "files": kind_counts.get("file", 0) + kind_counts.get("test", 0),
            "functions": kind_counts.get("function", 0) + kind_counts.get("method", 0),
            "classes": kind_counts.get("class", 0),
            "routes": kind_counts.get("route", 0),
            "pipelines": len(pipelines),
            "cycles": len(validation.get("import_cycles", [])) if validation else 0,
            "provenance": validation.get("provenance_counts", {}) if validation else {},
        },
        "nodes": nodes_out,
        "edges": edges_out,
        "fileCallLinks": file_call_links,
        "pipelines": pipelines,
        "dynamicSignals": graph.dynamic_signals,
    }


class Interactive3DExporter:
    """Generates a self-contained interactive 3D WebGL Architecture & Pipeline Explorer HTML."""

    @staticmethod
    def render(
        graph: DependencyGraph,
        validation: dict[str, Any] | None = None,
        include_external: bool = False,
        pipeline_depth: int = 8,
    ) -> str:
        payload = build_3d_payload(
            graph,
            validation=validation,
            include_external=include_external,
            pipeline_depth=pipeline_depth,
        )
        embedded_json = _safe_json_for_html(payload)
        title = f"Root-Cause Architect 3D — {payload['root']}"
        return _HTML_TEMPLATE.replace("__TITLE__", title).replace("__GRAPH_DATA__", embedded_json)


_HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>__TITLE__</title>
<style>
  :root {
    --bg: #060913;
    --panel: rgba(12, 18, 32, 0.90);
    --panel-border: rgba(148, 163, 184, 0.18);
    --text: #e2e8f0;
    --muted: #94a3b8;
    --accent: #38bdf8;
    --accent-2: #a78bfa;
    --rose: #f43f5e;
    --cyan: #22d3ee;
    --amber: #fbbf24;
    --emerald: #34d399;
    --mono: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    --sans: -apple-system, BlinkMacSystemFont, "Inter", "Segoe UI", Roboto, sans-serif;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  html, body {
    width: 100%; height: 100%; overflow: hidden;
    background: var(--bg); color: var(--text); font-family: var(--sans);
    font-size: 13px;
  }
  #graph-3d { position: fixed; inset: 0; width: 100%; height: 100%; }

  /* Top HUD */
  .topbar {
    position: fixed; top: 12px; left: 12px; right: 12px; z-index: 20;
    display: flex; align-items: center; gap: 10px; flex-wrap: wrap;
    background: var(--panel); border: 1px solid var(--panel-border);
    backdrop-filter: blur(12px); border-radius: 12px; padding: 8px 14px;
    box-shadow: 0 12px 32px rgba(0,0,0,0.45);
  }
  .brand { display: flex; align-items: center; gap: 8px; font-weight: 700; font-size: 14px; white-space: nowrap; }
  .brand-dot { width: 10px; height: 10px; border-radius: 50%; background: linear-gradient(135deg, var(--cyan), var(--accent-2)); box-shadow: 0 0 10px var(--cyan); }
  .repo-badge { font-family: var(--mono); font-size: 11px; color: var(--accent); background: rgba(56,189,248,0.12); padding: 2px 7px; border-radius: 6px; }

  .mode-group { display: flex; gap: 4px; background: rgba(15, 23, 42, 0.85); padding: 3px; border-radius: 8px; border: 1px solid var(--panel-border); }
  .mode-btn {
    border: none; background: transparent; color: var(--muted); cursor: pointer;
    padding: 5px 10px; border-radius: 6px; font-size: 12px; font-weight: 600; transition: all 0.15s;
  }
  .mode-btn:hover { color: var(--text); background: rgba(255,255,255,0.06); }
  .mode-btn.active { color: #06101f; background: linear-gradient(135deg, #38bdf8, #818cf8); }

  .search-wrap { position: relative; flex: 1; min-width: 190px; max-width: 340px; }
  .search-input {
    width: 100%; background: rgba(15,23,42,0.9); border: 1px solid var(--panel-border);
    color: var(--text); border-radius: 8px; padding: 6px 10px; font-size: 12px; outline: none;
  }
  .search-input:focus { border-color: var(--accent); }
  .search-results {
    position: absolute; top: 34px; left: 0; right: 0; max-height: 280px; overflow-y: auto;
    background: #0c1324; border: 1px solid var(--panel-border); border-radius: 8px;
    display: none; z-index: 50; box-shadow: 0 14px 30px rgba(0,0,0,0.6);
  }
  .search-item {
    padding: 7px 10px; cursor: pointer; border-bottom: 1px solid rgba(148,163,184,0.08);
    display: flex; align-items: center; justify-content: space-between; gap: 8px;
  }
  .search-item:hover { background: rgba(56,189,248,0.14); }
  .search-item-label { font-family: var(--mono); font-size: 11px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

  .stats-row { display: flex; gap: 6px; margin-left: auto; align-items: center; flex-wrap: wrap; }
  .stat-pill { font-size: 11px; color: var(--muted); background: rgba(30,41,59,0.7); padding: 3px 8px; border-radius: 999px; font-family: var(--mono); }
  .stat-pill strong { color: var(--text); }
  .hud-btn {
    background: rgba(30,41,59,0.85); border: 1px solid var(--panel-border); color: var(--text);
    padding: 5px 9px; border-radius: 7px; cursor: pointer; font-size: 11px; font-weight: 600;
  }
  .hud-btn:hover { border-color: var(--accent); color: var(--accent); }

  /* Left Sidebar */
  .sidebar-left {
    position: fixed; top: 68px; left: 12px; bottom: 12px; width: 276px; z-index: 15;
    background: var(--panel); border: 1px solid var(--panel-border);
    backdrop-filter: blur(12px); border-radius: 12px; display: flex; flex-direction: column;
    overflow: hidden; transition: transform 0.2s ease;
  }
  .sidebar-left.collapsed { transform: translateX(-292px); }
  .panel-section { padding: 11px 12px; border-bottom: 1px solid var(--panel-border); }
  .panel-title { font-size: 11px; text-transform: uppercase; letter-spacing: 0.08em; color: var(--muted); font-weight: 700; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center; }

  .filter-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 5px; }
  .filter-chip {
    display: flex; align-items: center; gap: 6px; font-size: 11px; cursor: pointer;
    padding: 4px 6px; border-radius: 6px; background: rgba(15,23,42,0.65); border: 1px solid transparent;
  }
  .filter-chip:hover { border-color: var(--panel-border); }
  .swatch { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }

  .pipeline-list { flex: 1; overflow-y: auto; padding: 8px 10px; display: flex; flex-direction: column; gap: 6px; }
  .pipeline-card {
    padding: 8px 9px; border-radius: 8px; cursor: pointer;
    background: rgba(15,23,42,0.75); border: 1px solid rgba(148,163,184,0.12);
    transition: all 0.15s;
  }
  .pipeline-card:hover { border-color: var(--cyan); background: rgba(34,211,238,0.08); }
  .pipeline-card.active { border-color: var(--cyan); background: rgba(34,211,238,0.16); box-shadow: 0 0 0 1px rgba(34,211,238,0.3); }
  .pipeline-name { font-family: var(--mono); font-size: 11px; font-weight: 600; color: var(--text); word-break: break-all; }
  .pipeline-meta { font-size: 10px; color: var(--muted); margin-top: 4px; display: flex; gap: 8px; }

  /* Right Inspector */
  .inspector {
    position: fixed; top: 68px; right: 12px; bottom: 12px; width: 340px; z-index: 15;
    background: var(--panel); border: 1px solid var(--panel-border);
    backdrop-filter: blur(12px); border-radius: 12px; display: none; flex-direction: column;
    overflow: hidden; box-shadow: 0 14px 36px rgba(0,0,0,0.5);
  }
  .inspector.open { display: flex; }
  .inspector-header { padding: 12px 14px; border-bottom: 1px solid var(--panel-border); display: flex; align-items: flex-start; justify-content: space-between; gap: 8px; }
  .inspector-body { flex: 1; overflow-y: auto; padding: 12px 14px; display: flex; flex-direction: column; gap: 12px; }
  .kind-badge { font-size: 10px; text-transform: uppercase; font-weight: 700; padding: 2px 6px; border-radius: 4px; letter-spacing: 0.06em; display: inline-block; }
  .node-title { font-family: var(--mono); font-size: 13px; font-weight: 700; margin-top: 4px; word-break: break-all; }
  .node-file { font-family: var(--mono); font-size: 11px; color: var(--muted); margin-top: 3px; word-break: break-all; }
  .action-row { display: flex; gap: 6px; flex-wrap: wrap; }
  .btn-primary {
    background: linear-gradient(135deg, #0ea5e9, #6366f1); border: none; color: #fff;
    padding: 6px 10px; border-radius: 7px; cursor: pointer; font-size: 11px; font-weight: 700;
  }
  .btn-primary:hover { filter: brightness(1.1); }
  .link-list { display: flex; flex-direction: column; gap: 5px; }
  .link-item {
    padding: 6px 8px; border-radius: 6px; background: rgba(15,23,42,0.75);
    border: 1px solid rgba(148,163,184,0.1); cursor: pointer; font-family: var(--mono); font-size: 11px;
    display: flex; flex-direction: column; gap: 2px;
  }
  .link-item:hover { border-color: var(--accent); background: rgba(56,189,248,0.1); }
  .prov-tag { font-size: 9px; padding: 1px 5px; border-radius: 4px; background: rgba(148,163,184,0.16); color: var(--muted); width: fit-content; }
  .prov-static_ast { background: rgba(52,211,153,0.16); color: var(--emerald); }
  .prov-static_structural { background: rgba(56,189,248,0.16); color: var(--accent); }
  .prov-static_heuristic { background: rgba(251,191,36,0.18); color: var(--amber); }

  /* Bottom Pipeline Stepper Dock */
  .stepper-dock {
    position: fixed; left: 300px; right: 364px; bottom: 12px; z-index: 18;
    background: var(--panel); border: 1px solid rgba(34,211,238,0.35);
    backdrop-filter: blur(14px); border-radius: 12px; padding: 10px 14px;
    display: none; flex-direction: column; gap: 8px;
    box-shadow: 0 12px 36px rgba(0,0,0,0.6);
  }
  .stepper-dock.open { display: flex; }
  .stepper-top { display: flex; align-items: center; justify-content: space-between; gap: 8px; flex-wrap: wrap; }
  .stepper-controls { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }
  .step-pills { display: flex; gap: 5px; overflow-x: auto; padding-bottom: 2px; }
  .step-pill {
    border: 1px solid var(--panel-border); background: rgba(15,23,42,0.85); color: var(--muted);
    padding: 4px 9px; border-radius: 999px; cursor: pointer; font-size: 11px; font-weight: 600; white-space: nowrap;
  }
  .step-pill.passed { border-color: rgba(56,189,248,0.45); color: var(--accent); }
  .step-pill.active { background: var(--cyan); color: #04131a; border-color: var(--cyan); }
  .step-trace-list {
    max-height: 110px; overflow-y: auto; display: flex; flex-direction: column; gap: 4px;
    border-top: 1px solid var(--panel-border); padding-top: 6px;
  }
  .trace-row {
    font-family: var(--mono); font-size: 11px; display: flex; align-items: center; gap: 6px;
    padding: 3px 6px; border-radius: 5px; background: rgba(15,23,42,0.7); cursor: pointer;
  }
  .trace-row:hover { background: rgba(34,211,238,0.14); }
  .cross-badge { font-size: 9px; background: rgba(244,63,94,0.2); color: #fda4af; padding: 1px 5px; border-radius: 4px; }

  .scale-banner {
    position: fixed; top: 68px; left: 50%; transform: translateX(-50%); z-index: 16;
    background: rgba(15, 23, 42, 0.92); border: 1px solid rgba(251, 191, 36, 0.45);
    color: #fde68a; padding: 6px 12px; border-radius: 999px; font-size: 11px;
    display: none; align-items: center; gap: 8px;
  }
  .offline-banner {
    position: fixed; inset: 0; display: none; align-items: center; justify-content: center;
    background: var(--bg); z-index: 100; padding: 24px; text-align: center;
  }
  @media (max-width: 1100px) {
    .stepper-dock { left: 12px; right: 12px; }
  }
</style>
</head>
<body>
<div id="graph-3d"></div>

<div class="offline-banner" id="offline-banner">
  <div style="max-width:520px;background:var(--panel);border:1px solid var(--panel-border);padding:24px;border-radius:12px;">
    <h2 style="margin-bottom:8px;">3D WebGL Library Unavailable Offline</h2>
    <p style="color:var(--muted);line-height:1.5;">
      This interactive 3D map loads <code>three</code> and <code>3d-force-graph</code> from CDN.
      Connect to the internet and reload, or inspect the embedded deterministic JSON graph via <code>analyze.py graph --output</code>.
    </p>
  </div>
</div>

<div class="topbar">
  <div class="brand">
    <span class="brand-dot"></span>
    <span>Root-Cause Architect 3D</span>
    <span class="repo-badge" id="repo-name"></span>
  </div>

  <div class="mode-group" id="mode-group">
    <button class="mode-btn" data-mode="file">File-to-File</button>
    <button class="mode-btn" data-mode="function">Function-to-Function</button>
    <button class="mode-btn" data-mode="full">Full 3D</button>
    <button class="mode-btn" data-mode="pipeline">Pipeline Stepper</button>
  </div>

  <div class="search-wrap">
    <input class="search-input" id="search-input" placeholder="Search file, function, class, route..." autocomplete="off" />
    <div class="search-results" id="search-results"></div>
  </div>

  <div class="stats-row">
    <span class="stat-pill" id="stat-nodes"></span>
    <span class="stat-pill" id="stat-edges"></span>
    <span class="stat-pill" id="stat-cycles"></span>
    <button class="hud-btn" id="btn-color-mode">Color: Kind</button>
    <button class="hud-btn" id="btn-reset-cam">Reset Cam</button>
    <button class="hud-btn" id="btn-toggle-left">Panel</button>
  </div>
</div>

<div class="scale-banner" id="scale-banner">
  <span id="scale-banner-text"></span>
  <button class="hud-btn" id="btn-dismiss-banner" style="padding:2px 7px;">OK</button>
</div>

<aside class="sidebar-left" id="sidebar-left">
  <div class="panel-section">
    <div class="panel-title"><span>Node Layers</span></div>
    <div class="filter-grid" id="node-filters"></div>
  </div>
  <div class="panel-section">
    <div class="panel-title"><span>Edge Relations</span></div>
    <div class="filter-grid" id="edge-filters"></div>
  </div>
  <div class="panel-section" style="padding-bottom:6px;border-bottom:none;">
    <div class="panel-title">
      <span>Discovered Pipelines</span>
      <span id="pipeline-count" style="font-family:var(--mono);color:var(--cyan);">0</span>
    </div>
  </div>
  <div class="pipeline-list" id="pipeline-list"></div>
</aside>

<aside class="inspector" id="inspector">
  <div class="inspector-header">
    <div>
      <span class="kind-badge" id="ins-kind"></span>
      <div class="node-title" id="ins-title"></div>
      <div class="node-file" id="ins-file"></div>
    </div>
    <button class="hud-btn" id="btn-close-inspector">✕</button>
  </div>
  <div class="inspector-body" id="ins-body"></div>
</aside>

<div class="stepper-dock" id="stepper-dock">
  <div class="stepper-top">
    <div>
      <span style="font-size:10px;text-transform:uppercase;color:var(--cyan);font-weight:700;letter-spacing:0.08em;">Pipeline Trace</span>
      <span id="stepper-title" style="font-family:var(--mono);font-weight:700;margin-left:8px;"></span>
    </div>
    <div class="stepper-controls">
      <button class="hud-btn" id="step-first">⏮</button>
      <button class="hud-btn" id="step-prev">◀ Prev</button>
      <button class="btn-primary" id="step-play">▶ Play</button>
      <button class="hud-btn" id="step-next">Next ▶</button>
      <button class="hud-btn" id="step-all">All</button>
      <label style="font-size:11px;color:var(--muted);display:flex;align-items:center;gap:4px;cursor:pointer;">
        <input type="checkbox" id="step-cumulative" checked /> Cumulative
      </label>
      <button class="hud-btn" id="step-exit">✕</button>
    </div>
  </div>
  <div class="step-pills" id="step-pills"></div>
  <div class="step-trace-list" id="step-trace-list"></div>
</div>

<script id="rca-graph-data" type="application/json">__GRAPH_DATA__</script>
<script src="https://unpkg.com/three@0.160.0/build/three.min.js"></script>
<script src="https://unpkg.com/3d-force-graph@1.73.4/dist/3d-force-graph.min.js"></script>
<script>
(function() {
  const DATA = JSON.parse(document.getElementById("rca-graph-data").textContent);
  if (typeof ForceGraph3D === "undefined") {
    document.getElementById("offline-banner").style.display = "flex";
    return;
  }

  const KIND_COLORS = {
    route: "#f43f5e",
    file: "#38bdf8",
    function: "#a78bfa",
    method: "#c084fc",
    class: "#fbbf24",
    interface: "#f59e0b",
    type: "#fb923c",
    test: "#34d399",
    external: "#64748b",
  };
  const REL_COLORS = {
    ROUTES_TO: "#fb7185",
    CALLS: "#22d3ee",
    FILE_CALLS: "#06b6d4",
    IMPORTS: "#3b82f6",
    DEFINES: "#475569",
    INHERITS: "#fbbf24",
    TESTS: "#10b981",
  };

  // Indexes
  const nodeMap = new Map(DATA.nodes.map(n => [n.id, n]));
  const outEdges = new Map();
  const inEdges = new Map();
  for (const e of DATA.edges) {
    if (!outEdges.has(e.source)) outEdges.set(e.source, []);
    if (!inEdges.has(e.target)) inEdges.set(e.target, []);
    outEdges.get(e.source).push(e);
    inEdges.get(e.target).push(e);
  }
  const signalsByFile = new Map();
  for (const s of DATA.dynamicSignals || []) {
    if (!signalsByFile.has(s.file_path)) signalsByFile.set(s.file_path, []);
    signalsByFile.get(s.file_path).push(s);
  }

  // Group color palette
  const groupColors = new Map();
  function colorForGroup(g) {
    if (!groupColors.has(g)) {
      let h = 0;
      for (let i = 0; i < g.length; i++) h = (h * 31 + g.charCodeAt(i)) % 360;
      groupColors.set(g, `hsl(${h}, 72%, 60%)`);
    }
    return groupColors.get(g);
  }

  // State
  const isLargeRepo = DATA.nodes.length > 1500;
  const state = {
    mode: isLargeRepo ? "file" : (DATA.stats.functions > 0 ? "full" : "file"),
    colorBy: "kind",
    selectedId: null,
    blastFocus: false,
    visibleKinds: new Set(["route", "file", "function", "method", "class", "interface", "type", "test", "external"]),
    visibleRels: new Set(["ROUTES_TO", "CALLS", "FILE_CALLS", "IMPORTS", "DEFINES", "INHERITS", "TESTS"]),
    activePipeline: null,
    pipelineStep: 0,
    cumulative: true,
    playTimer: null,
    activeNodeIds: new Set(),
    stepHighlightNodes: new Set(),
    stepHighlightEdges: new Set(),
    upstreamSet: new Set(),
    downstreamSet: new Set(),
  };

  // Populate top HUD stats
  document.getElementById("repo-name").textContent = DATA.root;
  document.getElementById("stat-nodes").innerHTML = `<strong>${DATA.stats.nodes}</strong> nodes (${DATA.stats.files}f / ${DATA.stats.functions}fn)`;
  document.getElementById("stat-edges").innerHTML = `<strong>${DATA.stats.edges}</strong> edges`;
  document.getElementById("stat-cycles").innerHTML = `<strong>${DATA.stats.cycles}</strong> cycles`;
  document.getElementById("pipeline-count").textContent = String(DATA.pipelines.length);

  if (isLargeRepo) {
    const b = document.getElementById("scale-banner");
    document.getElementById("scale-banner-text").textContent =
      `Large graph (${DATA.stats.nodes} nodes): started in File-to-File mode for smooth 3D FPS. Switch to Function-to-Function, Full 3D, or Pipeline Stepper anytime.`;
    b.style.display = "flex";
    document.getElementById("btn-dismiss-banner").onclick = () => (b.style.display = "none");
  }

  // Build filter chips
  const nodeFilterEl = document.getElementById("node-filters");
  for (const kind of ["route", "file", "function", "method", "class", "test"]) {
    const lbl = document.createElement("label");
    lbl.className = "filter-chip";
    lbl.innerHTML = `<input type="checkbox" checked data-kind="${kind}" /><span class="swatch" style="background:${KIND_COLORS[kind]}"></span><span>${kind}</span>`;
    lbl.querySelector("input").onchange = (ev) => {
      if (ev.target.checked) state.visibleKinds.add(kind); else state.visibleKinds.delete(kind);
      rebuildScene();
    };
    nodeFilterEl.appendChild(lbl);
  }
  const edgeFilterEl = document.getElementById("edge-filters");
  for (const rel of ["ROUTES_TO", "CALLS", "IMPORTS", "DEFINES", "INHERITS", "TESTS"]) {
    const lbl = document.createElement("label");
    lbl.className = "filter-chip";
    lbl.innerHTML = `<input type="checkbox" checked data-rel="${rel}" /><span class="swatch" style="background:${REL_COLORS[rel]}"></span><span>${rel}</span>`;
    lbl.querySelector("input").onchange = (ev) => {
      if (ev.target.checked) state.visibleRels.add(rel); else state.visibleRels.delete(rel);
      rebuildScene();
    };
    edgeFilterEl.appendChild(lbl);
  }

  // Client-side pipeline tracer for arbitrary selected nodes
  function tracePipelineClient(startId, maxDepth = 8) {
    const startNode = nodeMap.get(startId);
    if (!startNode) return null;
    let frontier = [startId];
    if (startNode.kind === "file" || startNode.kind === "test") {
      const defs = (outEdges.get(startId) || [])
        .filter(e => e.relation === "DEFINES")
        .map(e => e.target)
        .filter(tid => (outEdges.get(tid) || []).some(ce => ce.relation === "CALLS" || ce.relation === "ROUTES_TO"));
      if (defs.length) frontier = Array.from(new Set(defs)).sort();
    }
    const visited = new Set(frontier);
    const steps = [{ step: 0, nodes: [...frontier], edges: [] }];
    let totalEdges = 0;

    for (let s = 1; s <= maxDepth; s++) {
      const nextSet = new Set();
      const stepEdges = [];
      const seen = new Set();
      for (const src of frontier) {
        let outs = (outEdges.get(src) || []).filter(e => e.relation === "ROUTES_TO" || e.relation === "CALLS");
        if (!outs.length && nodeMap.get(src)?.kind === "file") {
          outs = (outEdges.get(src) || []).filter(e => e.relation === "IMPORTS" && nodeMap.get(e.target)?.kind !== "external");
        }
        for (const e of outs) {
          if (!nodeMap.has(e.target)) continue;
          if (visited.has(e.target) && !nextSet.has(e.target)) continue;
          const k = `${e.source}|${e.relation}|${e.target}`;
          if (seen.has(k)) continue;
          seen.add(k);
          nextSet.add(e.target);
          const sf = nodeMap.get(e.source)?.file;
          const tf = nodeMap.get(e.target)?.file;
          stepEdges.push({
            source: e.source,
            target: e.target,
            source_file: sf,
            target_file: tf,
            cross_file: Boolean(sf && tf && sf !== tf),
            relation: e.relation,
            provenance: e.provenance,
            line: e.line,
            raw_callee: e.rawCallee,
          });
        }
      }
      if (!nextSet.size) break;
      nextSet.forEach(id => visited.add(id));
      frontier = Array.from(nextSet).sort();
      totalEdges += stepEdges.length;
      steps.push({ step: s, nodes: frontier, edges: stepEdges });
    }
    return {
      id: startId,
      label: startNode.label,
      kind: startNode.kind,
      file_path: startNode.file,
      total_steps: steps.length,
      total_nodes: visited.size,
      total_edges: totalEdges,
      steps,
    };
  }

  // Render discovered pipelines list
  const pipeListEl = document.getElementById("pipeline-list");
  function renderPipelineList() {
    pipeListEl.innerHTML = "";
    if (!DATA.pipelines.length) {
      pipeListEl.innerHTML = `<div style="color:var(--muted);font-size:11px;padding:6px;">No multi-step routes/entrypoints discovered. Click any node in 3D and choose <strong>Trace Pipeline from Here</strong>.</div>`;
      return;
    }
    DATA.pipelines.forEach((p, idx) => {
      const card = document.createElement("div");
      card.className = "pipeline-card" + (state.activePipeline && state.activePipeline.id === p.id ? " active" : "");
      card.innerHTML = `
        <div class="pipeline-name">${escapeHtml(p.label)}</div>
        <div class="pipeline-meta">
          <span style="color:${KIND_COLORS[p.kind] || '#94a3b8'}">${p.kind}</span>
          <span>${p.total_steps} steps</span>
          <span>${p.total_nodes} nodes</span>
        </div>`;
      card.onclick = () => startPipeline(p);
      pipeListEl.appendChild(card);
    });
  }

  function escapeHtml(str) {
    return String(str ?? "").replace(/[&<>"']/g, m => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[m]));
  }

  // Initialize 3D Force Graph
  const container = document.getElementById("graph-3d");
  const Graph = ForceGraph3D()(container)
    .backgroundColor("#060913")
    .showNavInfo(false)
    .nodeLabel(n => {
      const filePart = n.file ? `<div style="color:#94a3b8;font-size:11px;">${escapeHtml(n.file)}${n.startLine ? ":" + n.startLine : ""}</div>` : "";
      return `<div style="background:rgba(10,15,28,0.95);border:1px solid rgba(148,163,184,0.25);padding:6px 9px;border-radius:7px;font-family:monospace;font-size:12px;">
        <div style="color:${KIND_COLORS[n.kind] || '#e2e8f0'};font-weight:700;">[${n.kind}] ${escapeHtml(n.label)}</div>
        ${filePart}
      </div>`;
    })
    .nodeVal(n => {
      if (n.id === state.selectedId) return 14;
      if (state.stepHighlightNodes.has(n.id)) return 11;
      if (n.kind === "route") return 9;
      if (n.kind === "file" || n.kind === "test") return Math.min(10, 4 + Math.sqrt((n.inDeg || 0) + (n.outDeg || 0)));
      return Math.min(7, 2.5 + Math.sqrt((n.inDeg || 0) + (n.outDeg || 0)));
    })
    .nodeColor(n => {
      if (state.mode === "pipeline" && state.activePipeline) {
        if (state.stepHighlightNodes.has(n.id)) return "#22d3ee";
        if (state.activeNodeIds.has(n.id)) return "#38bdf8";
        return "rgba(71,85,105,0.22)";
      }
      if (state.selectedId) {
        if (n.id === state.selectedId) return "#ffffff";
        if (state.upstreamSet.has(n.id)) return "#fbbf24";
        if (state.downstreamSet.has(n.id)) return "#22d3ee";
        if (state.blastFocus) return "rgba(71,85,105,0.18)";
      }
      return state.colorBy === "group" ? colorForGroup(n.group) : (KIND_COLORS[n.kind] || "#94a3b8");
    })
    .linkColor(l => {
      const ek = `${edgeSrc(l)}|${l.relation}|${edgeTgt(l)}`;
      if (state.mode === "pipeline" && state.activePipeline) {
        if (state.stepHighlightEdges.has(ek)) return "#22d3ee";
        if (state.activeNodeIds.has(edgeSrc(l)) && state.activeNodeIds.has(edgeTgt(l))) return "rgba(56,189,248,0.45)";
        return "rgba(71,85,105,0.08)";
      }
      if (state.selectedId && state.blastFocus) {
        const s = edgeSrc(l), t = edgeTgt(l);
        if (s === state.selectedId || t === state.selectedId) return REL_COLORS[l.relation] || "#38bdf8";
        return "rgba(71,85,105,0.08)";
      }
      return REL_COLORS[l.relation] || "#475569";
    })
    .linkOpacity(0.55)
    .linkWidth(l => {
      const ek = `${edgeSrc(l)}|${l.relation}|${edgeTgt(l)}`;
      if (state.stepHighlightEdges.has(ek)) return 2.8;
      if (l.relation === "FILE_CALLS") return Math.min(3.5, 1 + Math.log2(1 + (l.count || 1)));
      if (l.relation === "CALLS" || l.relation === "ROUTES_TO") return 1.3;
      return 0.7;
    })
    .linkDirectionalArrowLength(l => (l.relation === "DEFINES" ? 0 : 4.5))
    .linkDirectionalArrowRelPos(0.95)
    .linkDirectionalParticles(l => {
      const ek = `${edgeSrc(l)}|${l.relation}|${edgeTgt(l)}`;
      if (state.stepHighlightEdges.has(ek)) return 4;
      if (state.selectedId && (edgeSrc(l) === state.selectedId || edgeTgt(l) === state.selectedId)) return 2;
      if (state.mode === "function" && (l.relation === "CALLS" || l.relation === "ROUTES_TO")) return 1;
      return 0;
    })
    .linkDirectionalParticleSpeed(0.008)
    .linkDirectionalParticleWidth(2.6)
    .linkLabel(l => {
      if (l.relation === "FILE_CALLS") {
        const sample = (l.calls || []).slice(0, 6).map(c => `${escapeHtml(c.callerLabel)} → ${escapeHtml(c.calleeLabel)}`).join("<br/>");
        return `<div style="background:rgba(10,15,28,0.95);border:1px solid #22d3ee;padding:6px 9px;border-radius:7px;font-family:monospace;font-size:11px;">
          <div style="color:#22d3ee;font-weight:700;">${l.count} cross-file function call(s)</div>
          <div style="margin-top:4px;color:#cbd5e1;">${sample}</div>
        </div>`;
      }
      return `<div style="background:rgba(10,15,28,0.95);border:1px solid rgba(148,163,184,0.25);padding:4px 8px;border-radius:6px;font-family:monospace;font-size:11px;">
        ${l.relation} (${l.provenance || "static"})${l.line ? " @ L" + l.line : ""}
      </div>`;
    })
    .onNodeClick(n => selectNode(n.id, true))
    .onBackgroundClick(() => {
      if (state.mode !== "pipeline") {
        state.selectedId = null;
        state.blastFocus = false;
        state.upstreamSet.clear();
        state.downstreamSet.clear();
        document.getElementById("inspector").classList.remove("open");
        refreshColors();
      }
    });

  function edgeSrc(l) { return typeof l.source === "object" ? l.source.id : l.source; }
  function edgeTgt(l) { return typeof l.target === "object" ? l.target.id : l.target; }

  function buildSceneData() {
    let nodes = [];
    let links = [];

    if (state.mode === "file") {
      const keep = new Set(["file", "test", "route", "external"]);
      nodes = DATA.nodes.filter(n => keep.has(n.kind) && state.visibleKinds.has(n.kind)).map(n => ({ ...n }));
      const ids = new Set(nodes.map(n => n.id));
      for (const e of DATA.edges) {
        if (!state.visibleRels.has(e.relation)) continue;
        if (e.relation === "IMPORTS" || e.relation === "TESTS") {
          if (ids.has(e.source) && ids.has(e.target)) links.push({ ...e });
        } else if (e.relation === "ROUTES_TO") {
          const tgt = nodeMap.get(e.target);
          const tgtFileId = tgt?.file ? `file:${tgt.file}` : e.target;
          if (ids.has(e.source) && ids.has(tgtFileId)) {
            links.push({ ...e, target: tgtFileId });
          }
        }
      }
      if (state.visibleRels.has("CALLS")) {
        for (const fc of DATA.fileCallLinks) {
          if (ids.has(fc.source) && ids.has(fc.target)) links.push({ ...fc });
        }
      }
    } else if (state.mode === "function") {
      const fnEdges = DATA.edges.filter(
        e => (e.relation === "CALLS" || e.relation === "ROUTES_TO" || e.relation === "INHERITS") && state.visibleRels.has(e.relation)
      );
      const connectedIds = new Set();
      fnEdges.forEach(e => { connectedIds.add(e.source); connectedIds.add(e.target); });
      nodes = DATA.nodes
        .filter(n => connectedIds.has(n.id) && state.visibleKinds.has(n.kind))
        .map(n => ({ ...n }));
      const ids = new Set(nodes.map(n => n.id));
      links = fnEdges.filter(e => ids.has(e.source) && ids.has(e.target)).map(e => ({ ...e }));
    } else if (state.mode === "pipeline" && state.activePipeline) {
      const p = state.activePipeline;
      const pipeNodeIds = new Set();
      const pipeLinks = [];
      for (const st of p.steps) {
        st.nodes.forEach(id => pipeNodeIds.add(id));
        st.edges.forEach(e => {
          pipeNodeIds.add(e.source);
          pipeNodeIds.add(e.target);
          pipeLinks.push({ ...e });
        });
      }
      // Also attach owning file nodes so user sees which file each function belongs to
      for (const id of Array.from(pipeNodeIds)) {
        const n = nodeMap.get(id);
        if (n?.file && n.kind !== "file" && n.kind !== "test") {
          const fid = `file:${n.file}`;
          if (nodeMap.has(fid)) {
            pipeNodeIds.add(fid);
            pipeLinks.push({ source: fid, target: id, relation: "DEFINES", provenance: "static_ast" });
          }
        }
      }
      nodes = Array.from(pipeNodeIds).map(id => ({ ...nodeMap.get(id) })).filter(Boolean);
      links = pipeLinks;
    } else {
      // Full 3D connected graph
      nodes = DATA.nodes.filter(n => state.visibleKinds.has(n.kind)).map(n => ({ ...n }));
      const ids = new Set(nodes.map(n => n.id));
      links = DATA.edges
        .filter(e => state.visibleRels.has(e.relation) && ids.has(e.source) && ids.has(e.target))
        .map(e => ({ ...e }));
    }

    return { nodes, links };
  }

  function rebuildScene() {
    document.querySelectorAll(".mode-btn").forEach(b => {
      b.classList.toggle("active", b.dataset.mode === state.mode);
    });
    const scene = buildSceneData();
    Graph.graphData(scene);
    refreshColors();
  }

  function refreshColors() {
    Graph
      .nodeColor(Graph.nodeColor())
      .nodeVal(Graph.nodeVal())
      .linkColor(Graph.linkColor())
      .linkWidth(Graph.linkWidth())
      .linkDirectionalParticles(Graph.linkDirectionalParticles());
  }

  function flyToNode(nodeId) {
    const gData = Graph.graphData();
    const target = gData.nodes.find(n => n.id === nodeId);
    if (!target || target.x === undefined) return;
    const dist = 140;
    const hyp = Math.hypot(target.x, target.y, target.z) || 1;
    const ratio = 1 + dist / hyp;
    Graph.cameraPosition(
      { x: target.x * ratio, y: target.y * ratio, z: target.z * ratio },
      target,
      900
    );
  }

  function selectNode(nodeId, fly = false) {
    const node = nodeMap.get(nodeId);
    if (!node) return;
    state.selectedId = nodeId;
    state.upstreamSet.clear();
    state.downstreamSet.clear();
    (inEdges.get(nodeId) || []).forEach(e => state.upstreamSet.add(e.source));
    (outEdges.get(nodeId) || []).forEach(e => state.downstreamSet.add(e.target));

    // If node is not in current filtered scene, switch to Full 3D so user can see it
    const inScene = Graph.graphData().nodes.some(n => n.id === nodeId);
    if (!inScene && state.mode !== "pipeline") {
      state.mode = "full";
      rebuildScene();
    }
    renderInspector(node);
    refreshColors();
    if (fly) setTimeout(() => flyToNode(nodeId), 120);
  }

  function renderInspector(node) {
    const ins = document.getElementById("inspector");
    ins.classList.add("open");
    const badge = document.getElementById("ins-kind");
    badge.textContent = node.kind;
    badge.style.background = (KIND_COLORS[node.kind] || "#64748b") + "30";
    badge.style.color = KIND_COLORS[node.kind] || "#e2e8f0";
    document.getElementById("ins-title").textContent = node.label;
    document.getElementById("ins-file").textContent = node.file
      ? `${node.file}${node.startLine ? ` (L${node.startLine}${node.endLine ? "-L" + node.endLine : ""})` : ""}`
      : node.id;

    const incoming = (inEdges.get(node.id) || []).filter(e => e.relation !== "DEFINES");
    const outgoing = (outEdges.get(node.id) || []).filter(e => e.relation !== "DEFINES");
    const defined = (outEdges.get(node.id) || []).filter(e => e.relation === "DEFINES");
    const warnings = node.file ? (signalsByFile.get(node.file) || []) : [];

    const body = document.getElementById("ins-body");
    body.innerHTML = `
      <div class="action-row">
        <button class="btn-primary" id="ins-btn-trace">Trace Pipeline from Here</button>
        <button class="hud-btn" id="ins-btn-blast">${state.blastFocus ? "Unfocus Blast" : "Focus Blast"}</button>
      </div>
      ${node.params?.length ? `<div style="font-family:var(--mono);font-size:11px;color:var(--muted);">params: (${escapeHtml(node.params.join(", "))})</div>` : ""}
      ${warnings.length ? `<div><div class="panel-title" style="color:var(--amber);">Dynamic / Reflection Warnings (${warnings.length})</div>${warnings.map(w => `<div class="link-item" style="border-color:rgba(251,191,36,0.35);"><span>${escapeHtml(w.kind)} @ L${w.line}</span><span style="color:var(--muted);">${escapeHtml(w.detail)}</span></div>`).join("")}</div>` : ""}
      <div>
        <div class="panel-title">Upstream Callers / Importers (${incoming.length})</div>
        <div class="link-list" id="ins-in-list"></div>
      </div>
      <div>
        <div class="panel-title">Downstream Callees / Imports (${outgoing.length})</div>
        <div class="link-list" id="ins-out-list"></div>
      </div>
      ${defined.length ? `<div><div class="panel-title">Defined Symbols (${defined.length})</div><div class="link-list" id="ins-def-list"></div></div>` : ""}
    `;

    document.getElementById("ins-btn-trace").onclick = () => {
      const p = tracePipelineClient(node.id, 8);
      if (p) startPipeline(p);
    };
    document.getElementById("ins-btn-blast").onclick = () => {
      state.blastFocus = !state.blastFocus;
      renderInspector(node);
      refreshColors();
    };

    function populateList(elId, edges, isOut) {
      const el = document.getElementById(elId);
      if (!el) return;
      if (!edges.length) {
        el.innerHTML = `<div style="color:var(--muted);font-size:11px;">None detected statically</div>`;
        return;
      }
      edges.slice(0, 40).forEach(e => {
        const peerId = isOut ? e.target : e.source;
        const peer = nodeMap.get(peerId);
        if (!peer) return;
        const item = document.createElement("div");
        item.className = "link-item";
        item.innerHTML = `
          <div style="display:flex;justify-content:space-between;gap:6px;">
            <span style="color:${KIND_COLORS[peer.kind] || '#e2e8f0'};">${escapeHtml(peer.label)}</span>
            <span style="color:${REL_COLORS[e.relation] || '#94a3b8'};font-size:10px;">${e.relation}</span>
          </div>
          <div style="display:flex;justify-content:space-between;align-items:center;gap:6px;">
            <span style="color:var(--muted);font-size:10px;">${escapeHtml(peer.file || "")}${e.line ? " :L" + e.line : ""}</span>
            <span class="prov-tag prov-${e.provenance}">${e.provenance}</span>
          </div>`;
        item.onclick = () => selectNode(peerId, true);
        el.appendChild(item);
      });
    }

    populateList("ins-in-list", incoming, false);
    populateList("ins-out-list", outgoing, true);
    if (defined.length) populateList("ins-def-list", defined, true);
  }

  // Pipeline Stepper logic
  function startPipeline(pipeline) {
    stopPlayback();
    state.activePipeline = pipeline;
    state.mode = "pipeline";
    state.pipelineStep = 0;
    document.getElementById("stepper-dock").classList.add("open");
    document.getElementById("stepper-title").textContent = `${pipeline.label} (${pipeline.total_steps} steps)`;
    renderPipelineList();
    rebuildScene();
    applyPipelineStep(0);
  }

  function applyPipelineStep(stepIdx) {
    const p = state.activePipeline;
    if (!p || !p.steps.length) return;
    const clamped = Math.max(0, Math.min(stepIdx, p.steps.length - 1));
    state.pipelineStep = clamped;

    state.activeNodeIds.clear();
    state.stepHighlightNodes.clear();
    state.stepHighlightEdges.clear();

    const startIdx = state.cumulative ? 0 : clamped;
    for (let i = startIdx; i <= clamped; i++) {
      const st = p.steps[i];
      st.nodes.forEach(id => {
        state.activeNodeIds.add(id);
        const f = nodeMap.get(id)?.file;
        if (f && nodeMap.has(`file:${f}`)) state.activeNodeIds.add(`file:${f}`);
      });
      if (i === clamped) {
        st.nodes.forEach(id => state.stepHighlightNodes.add(id));
        st.edges.forEach(e => state.stepHighlightEdges.add(`${e.source}|${e.relation}|${e.target}`));
      }
    }

    // Render step pills
    const pillsEl = document.getElementById("step-pills");
    pillsEl.innerHTML = "";
    p.steps.forEach((st, idx) => {
      const btn = document.createElement("button");
      btn.className = "step-pill" + (idx === clamped ? " active" : (idx < clamped ? " passed" : ""));
      btn.textContent = `Step ${idx} (${st.nodes.length})`;
      btn.onclick = () => { stopPlayback(); applyPipelineStep(idx); };
      pillsEl.appendChild(btn);
    });

    // Render step trace rows
    const traceEl = document.getElementById("step-trace-list");
    const activeStep = p.steps[clamped];
    traceEl.innerHTML = "";
    if (clamped === 0) {
      activeStep.nodes.forEach(nid => {
        const n = nodeMap.get(nid);
        if (!n) return;
        const row = document.createElement("div");
        row.className = "trace-row";
        row.innerHTML = `<span style="color:var(--rose);font-weight:700;">ENTRY</span><span>${escapeHtml(n.label)}</span><span style="color:var(--muted);margin-left:auto;">${escapeHtml(n.file || "")}</span>`;
        row.onclick = () => selectNode(nid, true);
        traceEl.appendChild(row);
      });
    } else {
      activeStep.edges.forEach(e => {
        const sn = nodeMap.get(e.source);
        const tn = nodeMap.get(e.target);
        const row = document.createElement("div");
        row.className = "trace-row";
        row.innerHTML = `
          <span style="color:var(--accent);">${escapeHtml(sn ? sn.label : e.source)}</span>
          <span style="color:var(--muted);">─${e.relation}→</span>
          <span style="color:var(--cyan);font-weight:700;">${escapeHtml(tn ? tn.label : e.target)}</span>
          ${e.cross_file ? `<span class="cross-badge">cross-file</span>` : ""}
          <span class="prov-tag prov-${e.provenance}" style="margin-left:auto;">${e.provenance}${e.line ? " L" + e.line : ""}</span>`;
        row.onclick = () => selectNode(e.target, true);
        traceEl.appendChild(row);
      });
    }

    refreshColors();
    if (activeStep.nodes.length) {
      setTimeout(() => flyToNode(activeStep.nodes[0]), 180);
    }
  }

  function stopPlayback() {
    if (state.playTimer) {
      clearInterval(state.playTimer);
      state.playTimer = null;
      document.getElementById("step-play").textContent = "▶ Play";
    }
  }

  // Wire buttons
  document.querySelectorAll(".mode-btn").forEach(btn => {
    btn.onclick = () => {
      const m = btn.dataset.mode;
      if (m === "pipeline") {
        if (!state.activePipeline && DATA.pipelines.length) {
          startPipeline(DATA.pipelines[0]);
          return;
        }
        if (state.activePipeline) {
          document.getElementById("stepper-dock").classList.add("open");
        }
      } else {
        stopPlayback();
        document.getElementById("stepper-dock").classList.remove("open");
      }
      state.mode = m;
      rebuildScene();
    };
  });

  document.getElementById("step-first").onclick = () => { stopPlayback(); applyPipelineStep(0); };
  document.getElementById("step-prev").onclick = () => { stopPlayback(); applyPipelineStep(state.pipelineStep - 1); };
  document.getElementById("step-next").onclick = () => { stopPlayback(); applyPipelineStep(state.pipelineStep + 1); };
  document.getElementById("step-all").onclick = () => {
    stopPlayback();
    state.cumulative = true;
    document.getElementById("step-cumulative").checked = true;
    if (state.activePipeline) applyPipelineStep(state.activePipeline.steps.length - 1);
  };
  document.getElementById("step-cumulative").onchange = (ev) => {
    state.cumulative = ev.target.checked;
    applyPipelineStep(state.pipelineStep);
  };
  document.getElementById("step-play").onclick = () => {
    if (state.playTimer) { stopPlayback(); return; }
    if (!state.activePipeline) return;
    document.getElementById("step-play").textContent = "⏸ Pause";
    state.playTimer = setInterval(() => {
      const next = state.pipelineStep + 1;
      if (next >= state.activePipeline.steps.length) {
        stopPlayback();
      } else {
        applyPipelineStep(next);
      }
    }, 1500);
  };
  document.getElementById("step-exit").onclick = () => {
    stopPlayback();
    state.activePipeline = null;
    state.mode = isLargeRepo ? "file" : "full";
    document.getElementById("stepper-dock").classList.remove("open");
    renderPipelineList();
    rebuildScene();
  };

  document.getElementById("btn-color-mode").onclick = (ev) => {
    state.colorBy = state.colorBy === "kind" ? "group" : "kind";
    ev.target.textContent = state.colorBy === "kind" ? "Color: Kind" : "Color: Module";
    refreshColors();
  };
  document.getElementById("btn-reset-cam").onclick = () => Graph.zoomToFit(600, 60);
  document.getElementById("btn-toggle-left").onclick = () => {
    document.getElementById("sidebar-left").classList.toggle("collapsed");
  };
  document.getElementById("btn-close-inspector").onclick = () => {
    document.getElementById("inspector").classList.remove("open");
  };

  // Search autocomplete
  const searchInput = document.getElementById("search-input");
  const searchRes = document.getElementById("search-results");
  searchInput.oninput = () => {
    const q = searchInput.value.trim().toLowerCase();
    if (!q) { searchRes.style.display = "none"; return; }
    const hits = DATA.nodes
      .filter(n => n.label.toLowerCase().includes(q) || (n.file && n.file.toLowerCase().includes(q)))
      .slice(0, 25);
    searchRes.innerHTML = "";
    hits.forEach(h => {
      const div = document.createElement("div");
      div.className = "search-item";
      div.innerHTML = `<span class="search-item-label">${escapeHtml(h.label)}</span><span class="kind-badge" style="background:${(KIND_COLORS[h.kind]||'#64748b')}30;color:${KIND_COLORS[h.kind]||'#e2e8f0'}">${h.kind}</span>`;
      div.onclick = () => {
        searchRes.style.display = "none";
        searchInput.value = h.label;
        selectNode(h.id, true);
      };
      searchRes.appendChild(div);
    });
    searchRes.style.display = hits.length ? "block" : "none";
  };
  document.addEventListener("click", (ev) => {
    if (!ev.target.closest(".search-wrap")) searchRes.style.display = "none";
  });

  // Boot
  renderPipelineList();
  rebuildScene();
  setTimeout(() => Graph.zoomToFit(700, 80), 800);
})();
</script>
</body>
</html>
"""
