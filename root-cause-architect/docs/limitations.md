# Known Limitations

1. **JS/TS Semantic Resolution:** `JavaScriptParser` and `TypeScriptParser` currently perform stdlib structural regex extraction (`provenance: static_structural`) rather than full TypeScript Compiler API type resolution.
2. **Additional Languages:** Non-Python/JS/TS files are retained via `FallbackParser` with explicit `parse_limitations`; Go, Rust, Dart, Java, PHP, Ruby, and SQL parsers are planned for later phases.
3. **Static vs Runtime Provenance:** Phase 3 produces static call/import/route graphs (`static_ast`, `static_structural`, `static_heuristic`). Dynamic dispatch, reflection, and runtime-only wiring require Phase 4 runtime tracing or manual verification.
4. **Phases 4–8 Not Yet Implemented:** `engine/{dataflow,intelligence,execution,refactoring,verification,review,memory,reporting}/` and `scripts/{trace_flow,find_duplicates,find_dead_code,verify_fix,compare_behavior}.py` remain unimplemented placeholders until Phases 4–8 are built.
5. **YAML Loader Subset:** Without `PyYAML`, `engine/config_loader.py` supports standard block mappings/lists used in `config/*.yaml` (not anchors or flow-style YAML).
