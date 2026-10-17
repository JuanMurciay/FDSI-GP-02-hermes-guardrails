"""Proxy HTTPS con lista blanca (solo CONNECT). Usado por el nivel N2.

Variable ALLOW: sufijos de dominio permitidos separados por coma.
Cada decision se imprime como una linea JSON (ALLOW/DENY) para el registro.
"""
import json
import os
import socket
import sys
import threading
from datetime import datetime, timezone

ALLOW = [d.strip().lower() for d in os.environ.get("ALLOW", "").split(",") if d.strip()]
PUERTO = int(os.environ.get("PORT", "3128"))


def log(decision, host, extra=""):
    print(json.dumps({"t": datetime.now(timezone.utc).isoformat(), "decision": decision,
                      "host": host, "extra": extra}), flush=True)


def permitido(host):
    host = host.lower()
    return any(host == d or host.endswith("." + d) for d in ALLOW)


def puente(a, b):
    try:
        while (datos := a.recv(65536)):
            b.sendall(datos)
    except OSError:
        pass
    finally:
        for s in (a, b):
            try:
                s.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass


def atender(cliente):
    try:
        cabecera = b""
        while b"\r\n\r\n" not in cabecera and len(cabecera) < 8192:
            trozo = cliente.recv(4096)
            if not trozo:
                return
            cabecera += trozo
        primera = cabecera.split(b"\r\n", 1)[0].decode("latin1").split()
        if len(primera) < 2 or primera[0] != "CONNECT":
            host = primera[1] if len(primera) > 1 else "?"
            log("DENY", host, "metodo no permitido")
            cliente.sendall(b"HTTP/1.1 403 Forbidden\r\n\r\n")
            return
        host, _, puerto = primera[1].partition(":")
        if not permitido(host):
            log("DENY", host)
            cliente.sendall(b"HTTP/1.1 403 Forbidden\r\n\r\n")
            return
        destino = socket.create_connection((host, int(puerto or 443)), timeout=15)
        log("ALLOW", host)
        cliente.sendall(b"HTTP/1.1 200 Connection Established\r\n\r\n")
        t = threading.Thread(target=puente, args=(destino, cliente), daemon=True)
        t.start()
        puente(cliente, destino)
        t.join(timeout=1)
    except OSError as e:
        log("ERROR", "?", str(e))
    finally:
        cliente.close()


if __name__ == "__main__":
    srv = socket.socket()
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("0.0.0.0", PUERTO))
    srv.listen(64)
    print(json.dumps({"inicio": True, "allow": ALLOW}), flush=True)
    while True:
        c, _ = srv.accept()
        threading.Thread(target=atender, args=(c,), daemon=True).start()
