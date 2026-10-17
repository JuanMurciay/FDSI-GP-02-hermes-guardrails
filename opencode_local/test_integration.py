"""Comprueba que los perfiles generados conectan al MCP y separan los modos."""

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import run


class LocalIntegrationTests(unittest.TestCase):
    def test_provider_error_is_extracted_from_json_events(self):
        event = json.dumps({"type": "error", "error": {"data": {"message": "403 FreeTierError"}}})
        self.assertEqual(run.provider_error(event), "403 FreeTierError")

    def test_last_text_event_is_reported_as_answer(self):
        events = "\n".join((
            json.dumps({"type": "text", "part": {"text": "Voy a revisar"}}),
            json.dumps({"type": "tool_use", "part": {"tool": "lab_laboratorio_controlado"}}),
            json.dumps({"type": "text", "part": {"text": "Acceso bloqueado"}}),
        ))
        self.assertEqual(run.final_text(events), "Acceso bloqueado")

    def test_generated_profiles_enforce_different_private_read_results(self):
        (run.ROOT / "local").mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=run.ROOT / "local") as temporary:
            with patch.object(run, "LOCAL", Path(temporary)):
                for mode, expected in (("as-is", True), ("to-be", False)):
                    with self.subTest(mode=mode):
                        folder = run.prepare(mode, "privada")
                        config = json.loads((folder / "opencode.json").read_text(encoding="utf-8"))
                        self.assertEqual(config["permission"], {"*": "deny", "bash": "ask", "lab_*": "allow"})
                        server = config["mcp"]["lab"]
                        env = os.environ.copy()
                        env.update(server["environment"])
                        calls = [
                            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-06-18"}},
                            {"jsonrpc": "2.0", "method": "notifications/initialized"},
                            {"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {
                                "name": "laboratorio_controlado", "arguments": {
                                    "action": "read_file", "target": "privados/secreto.txt"}}},
                        ]
                        result = subprocess.run(server["command"], env=env,
                                                input="\n".join(map(json.dumps, calls)) + "\n",
                                                capture_output=True, text=True, timeout=10)
                        self.assertEqual(result.returncode, 0, result.stderr)
                        response = json.loads(result.stdout.splitlines()[-1])
                        outcome = json.loads(response["result"]["content"][0]["text"])
                        self.assertEqual(outcome["audit"]["allowed"], expected)
                        self.assertTrue((folder / "auditoria.jsonl").exists())


if __name__ == "__main__":
    unittest.main()
