"""Adaptador MCP stdio mínimo para que Hermes pueda llamar al supervisor externo.

MCP usa JSON-RPC 2.0 con un mensaje JSON por línea en stdio. Este adaptador es
experimental y debe validarse con la versión concreta de Hermes del equipo.
"""

import json
import os
import sys
from pathlib import Path

from supervisor import Supervisor


ROOT = Path(__file__).resolve().parents[1]
SUPERVISOR = Supervisor(ROOT / "datos", ROOT / "evidencias" / "mcp.jsonl")
MODE = os.environ.get("FDSI_MODE", "to-be")
TOOLS = [
    {
        "name": "laboratorio_controlado",
        "description": "Ejecuta una herramienta de laboratorio bajo la política externa. No usar datos reales.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["read_file", "write_file", "http_get"]},
                "target": {"type": "string"},
                "content": {"type": "string"},
            },
            "required": ["action", "target"],
        },
    }
]


def handle(message: dict) -> dict | None:
    method = message.get("method")
    request_id = message.get("id")
    if request_id is None:
        return None
    base = {"jsonrpc": "2.0", "id": request_id}
    if method == "initialize":
        base["result"] = {
            "protocolVersion": message.get("params", {}).get("protocolVersion", "2024-11-05"),
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "fdsi-guardrails", "version": "0.1.0"},
        }
    elif method == "tools/list":
        base["result"] = {"tools": TOOLS}
    elif method == "tools/call":
        params = message.get("params", {})
        if params.get("name") != "laboratorio_controlado":
            base["error"] = {"code": -32602, "message": "Herramienta desconocida"}
        else:
            try:
                args = params.get("arguments", {})
                outcome = SUPERVISOR.execute(
                    MODE, args["action"], args["target"], args.get("content", "")
                )
                base["result"] = {
                    "content": [{"type": "text", "text": json.dumps(outcome, ensure_ascii=False)}],
                    "isError": False,
                }
            except (KeyError, ValueError, TypeError) as error:
                base["error"] = {"code": -32602, "message": str(error)}
    else:
        base["error"] = {"code": -32601, "message": "Método no disponible"}
    return base


def main():
    for line in sys.stdin:
        try:
            response = handle(json.loads(line))
        except (json.JSONDecodeError, TypeError) as error:
            response = {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": str(error)}}
        if response is not None:
            sys.stdout.write(json.dumps(response, ensure_ascii=False) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
