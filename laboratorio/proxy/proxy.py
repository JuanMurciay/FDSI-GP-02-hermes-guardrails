"""Proxy con lista blanca (CONNECT HTTPS) y Broker de Credenciales (Secretless Broker) para N2.

Variables de entorno:
- ALLOW: sufijos de dominio permitidos para tunel CONNECT separados por coma.
- BROKER_HOSTS: dominios internos permitidos para inyeccion de credenciales HTTP (ej. api.lab).
- BROKER_SECRET: credencial que el proxy inyecta como 'Authorization: Bearer <secret>' en transito
  sin que el contenedor del agente conozca jamas su valor.
- BROKER_UPSTREAM: opcional 'host:puerto' real al que redirigir las peticiones de BROKER_HOSTS.
Cada decision se imprime como una linea JSON (ALLOW/BROKER_INJECT/DENY) para el registro.
"""
import json
import os
import socket
import threading
from datetime import datetime, timezone
from urllib.parse import urlsplit

ALLOW = [d.strip().lower() for d in os.environ.get("ALLOW", "").split(",") if d.strip()]
BROKER_HOSTS = [d.strip().lower() for d in os.environ.get("BROKER_HOSTS", "").split(",") if d.strip()]
BROKER_SECRET = os.environ.get("BROKER_SECRET", "")
BROKER_UPSTREAM = os.environ.get("BROKER_UPSTREAM", "")
PUERTO = int(os.environ.get("PORT", "3128"))


def log(decision, host, extra=""):
    print(json.dumps({"t": datetime.now(timezone.utc).isoformat(), "decision": decision,
                      "host": host, "extra": extra}), flush=True)


def _coincide(host, lista):
    host = host.lower()
    return any(host == d or host.endswith("." + d) for d in lista)


def permitido(host):
    return _coincide(host, ALLOW)


def permitido_broker(host):
    return bool(BROKER_SECRET) and _coincide(host, BROKER_HOSTS)


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


def manejar_broker_http(cliente, primera_linea, resto_cabecera, cuerpo_inicial):
    partes = primera_linea.split()
    if len(partes) < 3:
        cliente.sendall(b"HTTP/1.1 400 Bad Request\r\n\r\n")
        return
    metodo, url_raw, version = partes[0], partes[1], partes[2]
    parsed = urlsplit(url_raw)
    host = (parsed.hostname or "").lower()
    puerto = parsed.port or 80
    if not permitido_broker(host):
        log("DENY", host or url_raw, "metodo no permitido o host fuera del broker")
        cliente.sendall(b"HTTP/1.1 403 Forbidden\r\n\r\n")
        return

    ruta = parsed.path or "/"
    if parsed.query:
        ruta += "?" + parsed.query

    lineas_hdr = []
    for linea in resto_cabecera.decode("latin1").split("\r\n"):
        if not linea:
            continue
        nombre = linea.split(":", 1)[0].strip().lower()
        if nombre in ("authorization", "proxy-connection", "connection"):
            continue
        lineas_hdr.append(linea)
    lineas_hdr.append(f"Authorization: Bearer {BROKER_SECRET}")
    lineas_hdr.append("Connection: close")

    peticion_modificada = (
        f"{metodo} {ruta} {version}\r\n" + "\r\n".join(lineas_hdr) + "\r\n\r\n"
    ).encode("latin1") + cuerpo_inicial

    dest_host, dest_port = host, puerto
    if BROKER_UPSTREAM:
        uh, _, up = BROKER_UPSTREAM.partition(":")
        dest_host = uh
        dest_port = int(up or puerto)

    with socket.create_connection((dest_host, dest_port), timeout=15) as destino:
        log("BROKER_INJECT", host, f"{metodo} {ruta}")
        destino.sendall(peticion_modificada)
        while (resp := destino.recv(65536)):
            cliente.sendall(resp)


def atender(cliente):
    try:
        datos = b""
        while b"\r\n\r\n" not in datos and len(datos) < 16384:
            trozo = cliente.recv(4096)
            if not trozo:
                return
            datos += trozo
        cabecera, _, cuerpo_inicial = datos.partition(b"\r\n\r\n")
        primera_bytes, _, resto_cabecera = cabecera.partition(b"\r\n")
        primera_texto = primera_bytes.decode("latin1")
        primera = primera_texto.split()
        if len(primera) < 2:
            return
        if primera[0] != "CONNECT":
            return manejar_broker_http(cliente, primera_texto, resto_cabecera, cuerpo_inicial)

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
    print(json.dumps({"inicio": True, "allow": ALLOW, "broker_hosts": BROKER_HOSTS,
                      "broker_activo": bool(BROKER_SECRET)}), flush=True)
    while True:
        c, _ = srv.accept()
        threading.Thread(target=atender, args=(c,), daemon=True).start()
