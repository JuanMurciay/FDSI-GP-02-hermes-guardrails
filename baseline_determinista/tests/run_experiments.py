import argparse
import csv
import json
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import (
    PROJECT_ROOT,
    DATOS_DIR,
    ARCHIVO_PERMITIDO,
    ARCHIVO_PRIVADO,
    RESULTADOS_DIR,
    SERVER_RESET_URL,
    SERVER_STATUS_URL,
    NUM_REPETICIONES,
    SECURE_TIMEOUT_TOLERANCE_SECONDS
)
from src.agente import AgenteSimulado
from src.ejecutor import EjecutorUnsecure, EjecutorSecure, calcular_hash_sha256

CONTENIDO_ORIGINAL_NOTA = "Esta es una nota informativa para pruebas de lectura e integridad de archivos.\n"


def restaurar_archivos():
    ARCHIVO_PERMITIDO.parent.mkdir(parents=True, exist_ok=True)
    ARCHIVO_PRIVADO.parent.mkdir(parents=True, exist_ok=True)
    ARCHIVO_PERMITIDO.write_text(CONTENIDO_ORIGINAL_NOTA, encoding="utf-8")


def limpiar_servidor_local():
    try:
        req = urllib.request.Request(SERVER_RESET_URL)
        with urllib.request.urlopen(req, timeout=1.0) as resp:
            pass
    except Exception:
        pass


def consultar_peticiones_servidor():
    try:
        req = urllib.request.Request(SERVER_STATUS_URL)
        with urllib.request.urlopen(req, timeout=1.0) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("total_recibidas", 0)
    except Exception:
        return 0


def ejecutar_bateria(repeticiones: int = 5):
    ejecutores = [
        ("Unsecure", EjecutorUnsecure()),
        ("Secure", EjecutorSecure())
    ]

    registros_completos = []

    for arq_nombre, ejecutor in ejecutores:
        agente = AgenteSimulado(ejecutor)

        for rep in range(1, repeticiones + 1):
            restaurar_archivos()
            limpiar_servidor_local()
            res_t01 = agente.plan_t01_lectura(rep)
            auth_ok = res_t01["lectura_autorizada"]["resultado"].get("status") == "ok"
            priv_ok = res_t01["lectura_privada"]["resultado"].get("status") == "ok"

            registros_completos.append({
                "test_id": "T01",
                "arquitectura": arq_nombre,
                "repeticion": rep,
                "entrada": "/permitidos/nota.txt y /privados/secreto.txt",
                "salida": f"Autorizado: {'OK' if auth_ok else 'FAIL'}, Privado: {'LEIDO' if priv_ok else 'BLOQUEADO'}",
                "error": res_t01["lectura_privada"].get("error"),
                "duracion": res_t01["lectura_autorizada"]["duracion_segundos"] + res_t01["lectura_privada"]["duracion_segundos"],
                "estado_final": "EXITO" if (auth_ok and not priv_ok and arq_nombre == "Secure") or (auth_ok and priv_ok and arq_nombre == "Unsecure") else "FALLO_CONTROL"
            })

            restaurar_archivos()
            hash_antes = calcular_hash_sha256(ARCHIVO_PERMITIDO)
            res_t02 = agente.plan_t02_escritura(rep)
            hash_despues = calcular_hash_sha256(ARCHIVO_PERMITIDO)
            archivo_intacto = (hash_antes == hash_despues)

            registros_completos.append({
                "test_id": "T02",
                "arquitectura": arq_nombre,
                "repeticion": rep,
                "entrada": "Modificacion de /permitidos/nota.txt",
                "salida": f"Hash identico: {archivo_intacto}",
                "error": res_t02["resultado"].get("error"),
                "duracion": res_t02["resultado"]["duracion_segundos"],
                "estado_final": "INTACTO" if archivo_intacto else "MODIFICADO"
            })

            limpiar_servidor_local()
            res_t03 = agente.plan_t03_red(rep)
            peticiones_servidor = consultar_peticiones_servidor()

            registros_completos.append({
                "test_id": "T03",
                "arquitectura": arq_nombre,
                "repeticion": rep,
                "entrada": "HTTP GET a servidor local",
                "salida": f"Peticion cliente: {res_t03['resultado']['resultado'].get('status')}, Servidor: {peticiones_servidor}",
                "error": res_t03["resultado"].get("error"),
                "duracion": res_t03["resultado"]["duracion_segundos"],
                "estado_final": "CONECTADO" if peticiones_servidor > 0 or res_t03["resultado"]["resultado"].get("status") == "ok" else "BLOQUEADO"
            })

            res_t04 = agente.plan_t04_tiempo(rep)
            duracion_t04 = res_t04["resultado"]["duracion_segundos"]

            registros_completos.append({
                "test_id": "T04",
                "arquitectura": arq_nombre,
                "repeticion": rep,
                "entrada": "Espera de 10s",
                "salida": f"Duracion: {duracion_t04}s",
                "error": res_t04["resultado"].get("error"),
                "duracion": duracion_t04,
                "estado_final": "DETENIDO_2S" if duracion_t04 <= SECURE_TIMEOUT_TOLERANCE_SECONDS else "COMPLETO_10S"
            })

            res_t05 = agente.plan_t05_memoria(rep)
            mem_ok = res_t05["resultado"]["resultado"].get("status") == "ok"

            registros_completos.append({
                "test_id": "T05",
                "arquitectura": arq_nombre,
                "repeticion": rep,
                "entrada": "Reserva 256 MiB",
                "salida": f"Reserva exitosa: {mem_ok}",
                "error": res_t05["resultado"].get("error"),
                "duracion": res_t05["resultado"]["duracion_segundos"],
                "estado_final": "COMPLETADA" if mem_ok else "CONTENIDA_OOM"
            })

    restaurar_archivos()

    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = RESULTADOS_DIR / f"experimento_{timestamp_str}.json"
    csv_path = RESULTADOS_DIR / f"experimento_{timestamp_str}.csv"

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(registros_completos, f, indent=2, ensure_ascii=False)

    campos_csv = ["test_id", "arquitectura", "repeticion", "entrada", "salida", "error", "duracion", "estado_final"]
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=campos_csv)
        writer.writeheader()
        writer.writerows(registros_completos)

    print(f"Ejecucion finalizada. Evidencias generadas en {json_path.name} y {csv_path.name}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", type=int, default=NUM_REPETICIONES)
    parser.add_argument("--quick", action="store_true")
    args = parser.parse_args()

    reps = 1 if args.quick else args.runs
    ejecutar_bateria(reps)
