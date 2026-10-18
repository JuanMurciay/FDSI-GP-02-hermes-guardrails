"""Ejercita el servidor MCP real por stdio, sin simular su función handle."""

import json
import os
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SERVER = ROOT / "src" / "mcp_guardrail.py"


class MCPProcessTests(unittest.TestCase):
    def test_stdio_handshake_and_policy(self):
        env = os.environ.copy()
        env["FDSI_MODE"] = "as-is"
        calls = [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-06-18"}},
            {"jsonrpc": "2.0", "method": "notifications/initialized"},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
            {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {
                "name": "laboratorio_controlado", "arguments": {
                    "action": "read_file", "target": "privados/secreto.txt"}}},
        ]
        result = subprocess.run([sys.executable, str(SERVER)],
                                input="\n".join(json.dumps(item) for item in calls) + "\n",
                                text=True, capture_output=True, env=env, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        responses = [json.loads(line) for line in result.stdout.splitlines()]
        self.assertEqual([item["id"] for item in responses], [1, 2, 3])
        self.assertEqual(responses[1]["result"]["tools"][0]["name"], "laboratorio_controlado")
        outcome = json.loads(responses[2]["result"]["content"][0]["text"])
        self.assertTrue(outcome["audit"]["allowed"])
        self.assertIn("SECRETO_FICTICIO", outcome["result"])


if __name__ == "__main__":
    unittest.main()
