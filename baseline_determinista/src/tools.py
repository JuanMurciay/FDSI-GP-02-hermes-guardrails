import argparse
import json
import os
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path


def t01_leer_archivo(ruta: str) -> dict:
    inicio = time.perf_counter()
    resultado = {
        "tool": "T01_leer_archivo",
        "ruta": str(ruta),
        "status": "error",
        "contenido": None,
        "bytes_leidos": 0,
        "error": None,
        "duracion_segundos": 0.0
    }
    try:
        path_obj = Path(ruta)
        if not path_obj.exists():
            resultado["error"] = f"Archivo no encontrado: {ruta}"
            return resultado
        
        with open(path_obj, "r", encoding="utf-8", errors="replace") as f:
            contenido = f.read()
        
        resultado["status"] = "ok"
        resultado["contenido"] = contenido
        resultado["bytes_leidos"] = len(contenido.encode("utf-8"))
    except PermissionError as pe:
        resultado["error"] = f"Permiso denegado: {pe}"
    except Exception as e:
        resultado["error"] = f"{type(e).__name__}: {e}"
    finally:
        resultado["duracion_segundos"] = round(time.perf_counter() - inicio, 4)
    return resultado


def t02_escribir_archivo(ruta: str, contenido: str) -> dict:
    inicio = time.perf_counter()
    resultado = {
        "tool": "T02_escribir_archivo",
        "ruta": str(ruta),
        "status": "error",
        "bytes_escritos": 0,
        "error": None,
        "duracion_segundos": 0.0
    }
    try:
        path_obj = Path(ruta)
        with open(path_obj, "w", encoding="utf-8") as f:
            f.write(contenido)
            f.flush()
            os.fsync(f.fileno())
        
        resultado["status"] = "ok"
        resultado["bytes_escritos"] = len(contenido.encode("utf-8"))
    except PermissionError as pe:
        resultado["error"] = f"Permiso denegado para escribir: {pe}"
    except OSError as oe:
        resultado["error"] = f"Error de sistema de archivos: {oe}"
    except Exception as e:
        resultado["error"] = f"{type(e).__name__}: {e}"
    finally:
        resultado["duracion_segundos"] = round(time.perf_counter() - inicio, 4)
    return resultado


def t03_peticion_red(url: str, test_id: str = "T03_DEFAULT", timeout: float = 3.0) -> dict:
    inicio = time.perf_counter()
    resultado = {
        "tool": "T03_peticion_red",
        "url": url,
        "test_id": test_id,
        "status": "error",
        "http_code": None,
        "respuesta": None,
        "error": None,
        "duracion_segundos": 0.0
    }
    
    separator = "&" if "?" in url else "?"
    url_con_id = f"{url}{separator}id={test_id}" if "id=" not in url else url
    resultado["url_consultada"] = url_con_id

    try:
        req = urllib.request.Request(
            url_con_id,
            headers={"User-Agent": f"AgentTool/1.0 (ID: {test_id})"}
        )
        with urllib.request.urlopen(req, timeout=timeout) as response:
            body = response.read().decode("utf-8", errors="replace")
            resultado["status"] = "ok"
            resultado["http_code"] = response.getcode()
            resultado["respuesta"] = body
    except urllib.error.URLError as ue:
        resultado["error"] = f"Fallo de conexion: {ue.reason}"
    except TimeoutError:
        resultado["error"] = f"Tiempo de espera agotado ({timeout}s)"
    except Exception as e:
        resultado["error"] = f"{type(e).__name__}: {e}"
    finally:
        resultado["duracion_segundos"] = round(time.perf_counter() - inicio, 4)
    return resultado


def t04_espera_tiempo(segundos: float = 10.0) -> dict:
    inicio = time.perf_counter()
    resultado = {
        "tool": "T04_espera_tiempo",
        "segundos_solicitados": segundos,
        "status": "completado",
        "segundos_transcurridos": 0.0,
        "error": None,
        "duracion_segundos": 0.0
    }
    try:
        paso = 0.1
        acumulado = 0.0
        while acumulado < segundos:
            dormir = min(paso, segundos - acumulado)
            time.sleep(dormir)
            acumulado += dormir
        resultado["segundos_transcurridos"] = round(acumulado, 2)
    except Exception as e:
        resultado["status"] = "interrumpido"
        resultado["error"] = f"{type(e).__name__}: {e}"
    finally:
        duracion = round(time.perf_counter() - inicio, 4)
        resultado["duracion_segundos"] = duracion
        if resultado["segundos_transcurridos"] == 0.0:
            resultado["segundos_transcurridos"] = duracion
    return resultado


def t05_reserva_memoria(mb: int = 256, mantener_segundos: float = 1.0) -> dict:
    inicio = time.perf_counter()
    resultado = {
        "tool": "T05_reserva_memoria",
        "mb_solicitados": mb,
        "status": "error",
        "mb_reservados": 0,
        "error": None,
        "duracion_segundos": 0.0
    }
    try:
        total_bytes = mb * 1024 * 1024
        bloque = bytearray(total_bytes)
        for offset in range(0, total_bytes, 1024 * 1024):
            bloque[offset] = 0xAA
        resultado["mb_reservados"] = mb
        time.sleep(mantener_segundos)
        del bloque
        resultado["status"] = "ok"
    except MemoryError:
        resultado["error"] = f"MemoryError: Fallo al asignar {mb} MiB"
    except Exception as e:
        resultado["error"] = f"{type(e).__name__}: {e}"
    finally:
        resultado["duracion_segundos"] = round(time.perf_counter() - inicio, 4)
    return resultado


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--tool", required=True, choices=["T01", "T02", "T03", "T04", "T05"])
    parser.add_argument("--ruta", default="")
    parser.add_argument("--contenido", default="test_write")
    parser.add_argument("--url", default="http://127.0.0.1:8000/api/test")
    parser.add_argument("--test-id", default="CLI")
    parser.add_argument("--segundos", type=float, default=10.0)
    parser.add_argument("--mb", type=int, default=256)
    
    args = parser.parse_args()
    
    res = {}
    if args.tool == "T01":
        res = t01_leer_archivo(args.ruta)
    elif args.tool == "T02":
        res = t02_escribir_archivo(args.ruta, args.contenido)
    elif args.tool == "T03":
        res = t03_peticion_red(args.url, args.test_id)
    elif args.tool == "T04":
        res = t04_espera_tiempo(args.segundos)
    elif args.tool == "T05":
        res = t05_reserva_memoria(args.mb)
        
    print(json.dumps(res, indent=2, ensure_ascii=False))
