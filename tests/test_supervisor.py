import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from supervisor import Supervisor  # noqa: E402
from mcp_guardrail import handle  # noqa: E402


class SupervisorTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.data = Path(self.temporary.name) / "datos"
        (self.data / "permitidos").mkdir(parents=True)
        (self.data / "privados").mkdir()
        (self.data / "permitidos" / "nota.txt").write_text("nota original", encoding="utf-8")
        (self.data / "privados" / "secreto.txt").write_text("dato privado", encoding="utf-8")
        self.log = Path(self.temporary.name) / "audit.jsonl"
        self.supervisor = Supervisor(self.data, self.log)

    def test_legitimate_read_works_in_both_modes(self):
        for mode in ("as-is", "to-be"):
            result = self.supervisor.execute(mode, "read_file", "permitidos/nota.txt")
            self.assertTrue(result["audit"]["allowed"])
            self.assertEqual(result["result"], "nota original")

    def test_private_read_is_blocked_only_in_to_be(self):
        vulnerable = self.supervisor.execute("as-is", "read_file", "privados/secreto.txt")
        protected = self.supervisor.execute("to-be", "read_file", "privados/secreto.txt")
        self.assertIn("dato privado", vulnerable["result"])
        self.assertFalse(protected["audit"]["allowed"])
        self.assertIsNone(protected["result"])

    def test_write_is_blocked_and_original_remains_intact(self):
        result = self.supervisor.execute("to-be", "write_file", "permitidos/nota.txt", "cambio")
        self.assertFalse(result["audit"]["allowed"])
        self.assertEqual((self.data / "permitidos" / "nota.txt").read_text(encoding="utf-8"), "nota original")

    def test_path_escape_is_denied_in_both_modes(self):
        for mode in ("as-is", "to-be"):
            result = self.supervisor.execute(mode, "read_file", "../fuera.txt")
            self.assertFalse(result["audit"]["allowed"])
        records = [json.loads(line) for line in self.log.read_text(encoding="utf-8").splitlines()]
        self.assertEqual(len(records), 2)
        self.assertTrue(all(not record["allowed"] for record in records))

    def test_network_is_denied_in_to_be_without_request(self):
        result = self.supervisor.execute("to-be", "http_get", "http://127.0.0.1:8765/prueba")
        self.assertFalse(result["audit"]["allowed"])
        self.assertEqual(result["audit"]["reason"], "Red no autorizada")

    def test_other_hosts_are_denied_even_in_as_is(self):
        result = self.supervisor.execute("as-is", "http_get", "https://example.com/")
        self.assertFalse(result["audit"]["allowed"])


class MCPTests(unittest.TestCase):
    def test_initialize_and_list_tools(self):
        initialized = handle({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-06-18"}})
        self.assertEqual(initialized["result"]["protocolVersion"], "2025-06-18")
        listed = handle({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
        tool = listed["result"]["tools"][0]
        self.assertEqual(tool["name"], "laboratorio_controlado")
        self.assertNotIn("mode", tool["inputSchema"]["properties"])

    def test_notification_has_no_response(self):
        self.assertIsNone(handle({"jsonrpc": "2.0", "method": "notifications/initialized"}))


if __name__ == "__main__":
    unittest.main()
