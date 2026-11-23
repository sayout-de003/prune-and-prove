from __future__ import annotations

import ast

from engine.parsers.parser_registry import (
    CallInfo,
    DynamicSignal,
    ImportInfo,
    ParseResult,
    RouteInfo,
    SymbolInfo,
)


_HTTP_METHODS = {"get", "post", "put", "patch", "delete", "options", "head", "route", "api_route"}
_DYNAMIC_DECORATORS = {"receiver", "shared_task", "task", "register", "hookimpl", "fixture", "on_event"}
_DYNAMIC_CALLS = {"getattr", "setattr", "import_module", "__import__", "globals", "locals"}


def _dotted_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = _dotted_name(node.value)
        return f"{prefix}.{node.attr}" if prefix else node.attr
    if isinstance(node, ast.Call):
        return _dotted_name(node.func)
    if isinstance(node, ast.Subscript):
        return _dotted_name(node.value)
    return ""


def _const_str(node: ast.AST) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


class PythonParser:
    """Native Python AST parser producing static_ast symbols, imports, calls, routes, and dynamic signals."""

    name = "python_ast"

    def parse(self, file_path: str, source: str) -> ParseResult:
        result = ParseResult(
            file_path=file_path,
            language="python",
            parser_name=self.name,
            provenance="static_ast",
        )
        try:
            tree = ast.parse(source, filename=file_path)
        except SyntaxError as exc:
            result.errors.append(f"SyntaxError at line {exc.lineno}: {exc.msg}")
            return result

        self._visit_body(tree.body, file_path, [], result)
        return result

    def _visit_body(
        self,
        statements: list[ast.stmt],
        file_path: str,
        scope: list[str],
        result: ParseResult,
    ) -> None:
        caller = ".".join(scope) if scope else "<module>"
        for stmt in statements:
            if isinstance(stmt, ast.Import):
                for alias in stmt.names:
                    result.imports.append(
                        ImportInfo(
                            file_path=file_path,
                            module=alias.name,
                            alias=alias.asname,
                            level=0,
                            line=stmt.lineno,
                        )
                    )
            elif isinstance(stmt, ast.ImportFrom):
                module = stmt.module or ""
                names = [a.name for a in stmt.names]
                result.imports.append(
                    ImportInfo(
                        file_path=file_path,
                        module=module,
                        names=names,
                        level=stmt.level,
                        line=stmt.lineno,
                    )
                )
            elif isinstance(stmt, ast.ClassDef):
                qname = ".".join([*scope, stmt.name])
                bases = [b for b in (_dotted_name(base) for base in stmt.bases) if b]
                decorators = [d for d in (_dotted_name(dec) for dec in stmt.decorator_list) if d]
                result.symbols.append(
                    SymbolInfo(
                        name=stmt.name,
                        qualified_name=qname,
                        kind="class",
                        file_path=file_path,
                        start_line=stmt.lineno,
                        end_line=getattr(stmt, "end_lineno", stmt.lineno) or stmt.lineno,
                        bases=bases,
                        decorators=decorators,
                    )
                )
                self._check_decorators(stmt.decorator_list, qname, file_path, result)
                self._visit_body(stmt.body, file_path, [*scope, stmt.name], result)
            elif isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
                qname = ".".join([*scope, stmt.name])
                kind = "method" if scope else "function"
                params = [a.arg for a in stmt.args.posonlyargs + stmt.args.args + stmt.args.kwonlyargs]
                if stmt.args.vararg:
                    params.append(f"*{stmt.args.vararg.arg}")
                if stmt.args.kwarg:
                    params.append(f"**{stmt.args.kwarg.arg}")
                decorators = [d for d in (_dotted_name(dec) for dec in stmt.decorator_list) if d]
                result.symbols.append(
                    SymbolInfo(
                        name=stmt.name,
                        qualified_name=qname,
                        kind=kind,
                        file_path=file_path,
                        start_line=stmt.lineno,
                        end_line=getattr(stmt, "end_lineno", stmt.lineno) or stmt.lineno,
                        parameters=params,
                        decorators=decorators,
                    )
                )
                self._check_decorators(stmt.decorator_list, qname, file_path, result)
                self._extract_calls_in_node(stmt, qname, file_path, result)
                # Also discover nested functions/classes inside functions
                nested_defs = [
                    n for n in stmt.body if isinstance(n, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
                ]
                if nested_defs:
                    self._visit_body(nested_defs, file_path, [*scope, stmt.name], result)
            else:
                self._extract_calls_in_node(stmt, caller, file_path, result)

    def _check_decorators(
        self,
        decorators: list[ast.expr],
        handler_qname: str,
        file_path: str,
        result: ParseResult,
    ) -> None:
        for dec in decorators:
            dec_name = _dotted_name(dec)
            tail = dec_name.split(".")[-1] if dec_name else ""
            if tail in _HTTP_METHODS and isinstance(dec, ast.Call) and dec.args:
                route_path = _const_str(dec.args[0])
                if route_path is not None:
                    result.routes.append(
                        RouteInfo(
                            file_path=file_path,
                            method=tail.upper() if tail not in {"route", "api_route"} else "ANY",
                            path=route_path,
                            handler=handler_qname,
                            line=dec.lineno,
                        )
                    )
            if tail in _DYNAMIC_DECORATORS:
                result.dynamic_signals.append(
                    DynamicSignal(
                        file_path=file_path,
                        kind="decorator_registration",
                        detail=f"@{dec_name} on {handler_qname}",
                        line=dec.lineno,
                    )
                )

    def _extract_calls_in_node(
        self,
        node: ast.AST,
        caller: str,
        file_path: str,
        result: ParseResult,
    ) -> None:
        for child in ast.walk(node):
            # Do not attribute calls inside nested defs to the outer function
            if child is not node and isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                continue
            if not isinstance(child, ast.Call):
                continue
            callee = _dotted_name(child.func)
            if not callee:
                continue
            result.calls.append(
                CallInfo(
                    file_path=file_path,
                    caller=caller,
                    callee=callee,
                    line=child.lineno,
                    provenance="static_ast",
                )
            )
            tail = callee.split(".")[-1]
            if tail in _DYNAMIC_CALLS:
                result.dynamic_signals.append(
                    DynamicSignal(
                        file_path=file_path,
                        kind="dynamic_import" if "import" in tail else "reflection",
                        detail=f"{callee}(...) in {caller}",
                        line=child.lineno,
                    )
                )
            # Django urls.py path("route/", view)
            if tail in {"path", "re_path"} and len(child.args) >= 2:
                route_path = _const_str(child.args[0])
                handler = _dotted_name(child.args[1])
                if route_path is not None and handler:
                    result.routes.append(
                        RouteInfo(
                            file_path=file_path,
                            method="ANY",
                            path=route_path,
                            handler=handler,
                            line=child.lineno,
                        )
                    )
