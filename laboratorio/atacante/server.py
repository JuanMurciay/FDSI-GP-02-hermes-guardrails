"""Servidor del atacante (laboratorio). Registra todo lo que recibe; no hace nada mas.

GET /status -> historial de peticiones; GET /reset -> limpia el historial.
Cualquier otra ruta (por ejemplo /collect?id=...&d=...) se registra con query y cuerpo.
"""
import json
import sys
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

HISTORIAL = []


class Handler(BaseHTTPRequestHandler):
    def _json(self, code, datos):
        cuerpo = json.dumps(datos).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(cuerpo)))
        self.end_headers()
        self.wfile.write(cuerpo)

    def _manejar(self, metodo):
        url = urlparse(self.path)
        largo = int(self.headers.get("Content-Length", 0) or 0)
        cuerpo = self.rfile.read(largo).decode("utf-8", "replace") if largo else ""
        if url.path == "/status":
            return self._json(200, {"total": len(HISTORIAL), "historial": HISTORIAL})
        if url.path == "/reset":
            HISTORIAL.clear()
            return self._json(200, {"total": 0})
        q = parse_qs(url.query)
        HISTORIAL.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metodo": metodo,
            "path": url.path,
            "id": q.get("id", [""])[0],
            "query": q,
            "cuerpo": cuerpo,
            "cliente": self.client_address[0],
            "user_agent": self.headers.get("User-Agent", ""),
        })
        self._json(200, {"ok": True})

    def do_GET(self):
        self._manejar("GET")

    def do_POST(self):
        self._manejar("POST")

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    puerto = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    ThreadingHTTPServer(("0.0.0.0", puerto), Handler).serve_forever()
