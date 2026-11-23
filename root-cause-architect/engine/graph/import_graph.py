from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Iterable

from engine.parsers.parser_registry import ImportInfo, ParseResult


_JS_EXTENSIONS = (".ts", ".tsx", ".js", ".jsx", ".mts", ".mjs", ".cjs")


@dataclass(frozen=True)
class ResolvedImport:
    source_file: str
    target_file: str | None  # None when external or unresolved
    module: str
    names: tuple[str, ...]
    external: bool
    line: int
    provenance: str


class ImportGraph:
    """Resolves Python and JS/TS imports into internal file-to-file and external edges."""

    def __init__(self, known_files: Iterable[str]) -> None:
        self.known_files = set(known_files)
        self.edges: list[ResolvedImport] = []
        self._by_source: dict[str, list[ResolvedImport]] = {}
        self._by_target: dict[str, list[ResolvedImport]] = {}

    def build(self, results: Iterable[ParseResult]) -> list[ResolvedImport]:
        for res in results:
            for imp in res.imports:
                target = self._resolve_import(res.file_path, res.language, imp)
                edge = ResolvedImport(
                    source_file=res.file_path,
                    target_file=target,
                    module=imp.module,
                    names=tuple(imp.names),
                    external=target is None,
                    line=imp.line,
                    provenance=res.provenance,
                )
                self.edges.append(edge)
                self._by_source.setdefault(res.file_path, []).append(edge)
                if target:
                    self._by_target.setdefault(target, []).append(edge)
        return self.edges

    def imports_of(self, file_path: str) -> list[ResolvedImport]:
        return list(self._by_source.get(file_path, []))

    def importers_of(self, file_path: str) -> list[ResolvedImport]:
        return list(self._by_target.get(file_path, []))

    def _resolve_import(
        self,
        source_file: str,
        language: str | None,
        imp: ImportInfo,
    ) -> str | None:
        if language == "python":
            return self._resolve_python(source_file, imp)
        if language in {"javascript", "typescript", "javascript_react", "typescript_react"}:
            return self._resolve_js(source_file, imp)
        return None

    def _resolve_python(self, source_file: str, imp: ImportInfo) -> str | None:
        source_dir = PurePosixPath(source_file).parent

        if imp.level > 0:
            base = source_dir
            for _ in range(imp.level - 1):
                base = base.parent
            parts = [p for p in imp.module.split(".") if p]
            candidate_base = base.joinpath(*parts) if parts else base
            found = self._match_python_module(candidate_base)
            if found:
                return found
            # `from . import foo` where foo is a submodule
            for name in imp.names:
                sub = self._match_python_module(candidate_base / name)
                if sub:
                    return sub
            return None

        parts = [p for p in imp.module.split(".") if p]
        if not parts:
            return None

        # Try from repository root and common src/ layout
        for prefix in (PurePosixPath(), PurePosixPath("src")):
            candidate_base = prefix.joinpath(*parts)
            found = self._match_python_module(candidate_base)
            if found:
                return found
            # `from pkg.mod import submod`
            for name in imp.names:
                sub = self._match_python_module(candidate_base / name)
                if sub:
                    return sub
        return None

    def _match_python_module(self, path_base: PurePosixPath) -> str | None:
        raw = path_base.as_posix().lstrip("./")
        if not raw or raw == ".":
            return None
        for candidate in (f"{raw}.py", f"{raw}/__init__.py"):
            if candidate in self.known_files:
                return candidate
        return None

    def _resolve_js(self, source_file: str, imp: ImportInfo) -> str | None:
        if not imp.module.startswith("."):
            return None
        source_dir = PurePosixPath(source_file).parent
        joined = self._normalize_posix(source_dir / imp.module)
        if joined in self.known_files:
            return joined
        for ext in _JS_EXTENSIONS:
            if f"{joined}{ext}" in self.known_files:
                return f"{joined}{ext}"
            if f"{joined}/index{ext}" in self.known_files:
                return f"{joined}/index{ext}"
        return None

    @staticmethod
    def _normalize_posix(path: PurePosixPath) -> str:
        parts: list[str] = []
        for part in path.parts:
            if part in ("", "."):
                continue
            if part == "..":
                if parts:
                    parts.pop()
            else:
                parts.append(part)
        return "/".join(parts)
