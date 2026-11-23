from __future__ import annotations

import unittest
from pathlib import Path

from engine.parsers.parser_registry import ParserRegistry


FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"
PYTHON_FIXTURE = FIXTURES / "python-project"
TS_FIXTURE = FIXTURES / "typescript-project"


class ParserTests(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = ParserRegistry()

    def test_python_parser_extracts_symbols_calls_routes_and_dynamic_signals(self) -> None:
        res_main = self.registry.parse_file(PYTHON_FIXTURE, "app/main.py", "python")
        self.assertEqual(res_main.provenance, "static_ast")
        self.assertEqual(len(res_main.routes), 1)
        self.assertEqual(res_main.routes[0].path, "/api/payments")
        self.assertEqual(res_main.routes[0].handler, "create_payment")

        res_svc = self.registry.parse_file(PYTHON_FIXTURE, "app/services/payment.py", "python")
        qnames = {s.qualified_name for s in res_svc.symbols}
        self.assertIn("PaymentService", qnames)
        self.assertIn("PaymentService.process_payment", qnames)
        self.assertIn("on_payment_webhook", qnames)

        # Dynamic registration (@register) and reflection (getattr) must be captured
        sig_kinds = {s.kind for s in res_svc.dynamic_signals}
        self.assertIn("decorator_registration", sig_kinds)
        self.assertIn("reflection", sig_kinds)

    def test_typescript_parser_extracts_interfaces_functions_imports_and_routes(self) -> None:
        res_server = self.registry.parse_file(TS_FIXTURE, "src/server.ts", "typescript")
        self.assertEqual(res_server.provenance, "static_structural")
        self.assertTrue(any(i.module == "./routes/orders" for i in res_server.imports))
        self.assertTrue(any(r.path == "/orders" and r.handler == "handleOrder" for r in res_server.routes))

        res_orders = self.registry.parse_file(TS_FIXTURE, "src/routes/orders.ts", "typescript")
        kinds = {s.name: s.kind for s in res_orders.symbols}
        self.assertEqual(kinds.get("OrderPayload"), "interface")
        self.assertEqual(kinds.get("handleOrder"), "function")

    def test_fallback_parser_reports_limitation_without_crashing(self) -> None:
        res = self.registry.parse_file(PYTHON_FIXTURE, "pyproject.toml", "toml")
        self.assertEqual(res.parser_name, "fallback")
        self.assertTrue(res.limitations)
        self.assertEqual(res.errors, [])


if __name__ == "__main__":
    unittest.main()
