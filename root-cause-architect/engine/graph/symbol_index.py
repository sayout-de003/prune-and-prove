from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from engine.parsers.parser_registry import ParseResult, SymbolInfo


def symbol_id(file_path: str, qualified_name: str) -> str:
    return f"{file_path}::{qualified_name}"


@dataclass(frozen=True)
class IndexedSymbol:
    id: str
    info: SymbolInfo


class SymbolIndex:
    """Fast lookup index over all parsed symbols in a repository."""

    def __init__(self) -> None:
        self._by_id: dict[str, IndexedSymbol] = {}
        self._by_file: dict[str, list[IndexedSymbol]] = {}
        self._by_name: dict[str, list[IndexedSymbol]] = {}
        self._by_qname: dict[str, list[IndexedSymbol]] = {}

    def add_parse_results(self, results: Iterable[ParseResult]) -> None:
        for res in results:
            for sym in res.symbols:
                sid = symbol_id(sym.file_path, sym.qualified_name)
                entry = IndexedSymbol(id=sid, info=sym)
                self._by_id[sid] = entry
                self._by_file.setdefault(sym.file_path, []).append(entry)
                self._by_name.setdefault(sym.name, []).append(entry)
                self._by_qname.setdefault(sym.qualified_name, []).append(entry)

    def get(self, sid: str) -> IndexedSymbol | None:
        return self._by_id.get(sid)

    def in_file(self, file_path: str) -> list[IndexedSymbol]:
        return list(self._by_file.get(file_path, []))

    def find_by_name(self, name: str) -> list[IndexedSymbol]:
        return list(self._by_name.get(name, []))

    def find_by_qualified_name(self, qname: str) -> list[IndexedSymbol]:
        return list(self._by_qname.get(qname, []))

    def resolve_in_file(self, file_path: str, name: str) -> IndexedSymbol | None:
        direct = self._by_id.get(symbol_id(file_path, name))
        if direct:
            return direct
        for entry in self._by_file.get(file_path, []):
            if entry.info.name == name:
                return entry
        return None

    def all_symbols(self) -> list[IndexedSymbol]:
        return list(self._by_id.values())

    def __len__(self) -> int:
        return len(self._by_id)
