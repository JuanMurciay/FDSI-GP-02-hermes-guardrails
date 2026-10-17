import argparse
import json
from datetime import datetime, timezone
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse, parse_qs

HISTORIAL_PETICIONES = []
LOG_FILE = Path(__file__).resolve().parent / "logs_acceso.log"


class TestHTTPHandler(BaseHTTPRequestHandler):
    server_version = "TestServer/1.0"

    def _responder_json(self, status_code: int, datos: dict):
        respuesta = json.dumps(datos, indent=2).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(respuesta)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(respuesta)

    def _registrar_peticion(self, metodo: str):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        test_id = params.get("id", ["NO_ID"])[0]

        registro = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metodo": metodo,
            "path": parsed.path,
            "test_id": test_id,
            "query_params": params,
            "client_address": self.client_address[0],
            "user_agent": self.headers.get("User-Agent", "")
        }
        HISTORIAL_PETICIONES.append(registro)

        try:
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(registro) + "\n")
        except Exception:
            pass

        print(f"[{registro['timestamp']}] {metodo} {parsed.path} | id: {test_id} | IP: {self.client_address[0]}")
        return registro

    def do_GET(self):
        parsed = urlparse(self.path)
        registro = self._registrar_peticion("GET")

        if parsed.path == "/reset":
            HISTORIAL_PETICIONES.clear()
            if LOG_FILE.exists():
                LOG_FILE.write_text("", encoding="utf-8")
            self._responder_json(200, {
                "status": "ok",
                "mensaje": "Registros reiniciados",
                "total_registros": 0
            })
            return

        if parsed.path in ["/metricas", "/status"]:
            self._responder_json(200, {
                "status": "ok",
                "total_recibidas": len(HISTORIAL_PETICIONES),
                "historial": HISTORIAL_PETICIONES
            })
            return

        self._responder_json(200, {
            "status": "ok",
            "mensaje": "Peticion recibida",
            "test_id": registro["test_id"],
            "timestamp": registro["timestamp"]
        })

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8", errors="replace") if content_length > 0 else ""
        registro = self._registrar_peticion("POST")
        registro["body"] = body

        self._responder_json(200, {
            "status": "ok",
            "test_id": registro["test_id"],
            "body_length": len(body)
        })

    def log_message(self, format, *args):
        pass


def run_server(host: str = "127.0.0.1", port: int = 8000):
    servidor = HTTPServer((host, port), TestHTTPHandler)
    print(f"Servidor HTTP escuchando en http://{host}:{port}")
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        servidor.server_close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    run_server(args.host, args.port)
