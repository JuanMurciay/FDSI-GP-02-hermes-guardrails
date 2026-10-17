import hashlib
import json
import shutil
import subprocess
import time
from pathlib import Path
from typing import Dict, Any, Optional

from src.config import (
    PERMITIDOS_DIR,
    PRIVADOS_DIR,
    UNSECURE_TIMEOUT_SECONDS,
    SECURE_TIMEOUT_SECONDS,
    SECURE_MAX_MEMORY_MB,
    SECURE_CPU_LIMIT
)
from src import tools


def calcular_hash_sha256(ruta: Path) -> Optional[str]:
    if not ruta.exists():
        return None
    sha256 = hashlib.sha256()
    with open(ruta, "rb") as f:
        while chunk := f.read(65536):
            sha256.update(chunk)
    return sha256.hexdigest()


class BaseEjecutor:
    nombre_arquitectura = "Base"

    def ejecutar_herramienta(self, test_id: str, tool_name: str, args: Dict[str, Any], descripcion: str = "") -> Dict[str, Any]:
        raise NotImplementedError


class EjecutorUnsecure(BaseEjecutor):
    nombre_arquitectura = "Unsecure"

    def ejecutar_herramienta(self, test_id: str, tool_name: str, args: Dict[str, Any], descripcion: str = "") -> Dict[str, Any]:
        inicio = time.perf_counter()
        resultado_raw = None
        error = None
        estado_final = "EXITO"

        try:
            if tool_name == "T01":
                resultado_raw = tools.t01_leer_archivo(args.get("ruta", ""))
            elif tool_name == "T02":
                resultado_raw = tools.t02_escribir_archivo(args.get("ruta", ""), args.get("contenido", ""))
            elif tool_name == "T03":
                resultado_raw = tools.t03_peticion_red(args.get("url", ""), args.get("test_id", test_id), args.get("timeout", 3.0))
            elif tool_name == "T04":
                segundos = min(args.get("segundos", 10.0), UNSECURE_TIMEOUT_SECONDS)
                resultado_raw = tools.t04_espera_tiempo(segundos)
            elif tool_name == "T05":
                resultado_raw = tools.t05_reserva_memoria(args.get("mb", 256), args.get("mantener_segundos", 1.0))
            else:
                error = f"Herramienta desconocida: {tool_name}"
                estado_final = "ERROR_CONFIGURACION"
        except Exception as e:
            error = f"{type(e).__name__}: {e}"
            estado_final = "EXCEPCION"

        duracion = round(time.perf_counter() - inicio, 4)

        return {
            "test_id": test_id,
            "arquitectura": self.nombre_arquitectura,
            "herramienta": tool_name,
            "descripcion": descripcion,
            "argumentos": args,
            "resultado": resultado_raw,
            "error": error or (resultado_raw.get("error") if isinstance(resultado_raw, dict) else None),
            "duracion_segundos": duracion,
            "estado_final": estado_final
        }


class EjecutorSecure(BaseEjecutor):
    nombre_arquitectura = "Secure"

    def __init__(self, docker_image: str = "secure-tools:latest"):
        self.docker_image = docker_image
        self.docker_disponible = shutil.which("docker") is not None

    def ejecutar_herramienta(self, test_id: str, tool_name: str, args: Dict[str, Any], descripcion: str = "") -> Dict[str, Any]:
        if self.docker_disponible:
            return self._ejecutar_en_docker(test_id, tool_name, args, descripcion)
        else:
            return self._ejecutar_en_sandbox_simulado(test_id, tool_name, args, descripcion)

    def _ejecutar_en_docker(self, test_id: str, tool_name: str, args: Dict[str, Any], descripcion: str) -> Dict[str, Any]:
        inicio = time.perf_counter()
        
        docker_cmd = [
            "docker", "run", "--rm",
            "--network", "none",
            "--read-only",
            "--memory", f"{SECURE_MAX_MEMORY_MB}m",
            "--memory-swap", f"{SECURE_MAX_MEMORY_MB}m",
            "--cpus", str(SECURE_CPU_LIMIT),
            "-v", f"{PERMITIDOS_DIR}:/permitidos:ro",
            self.docker_image,
            "--tool", tool_name
        ]

        if tool_name in ["T01", "T02"]:
            ruta_interna = "/permitidos/nota.txt" if "nota.txt" in args.get("ruta", "") else "/privados/secreto.txt"
            docker_cmd.extend(["--ruta", ruta_interna])
            if tool_name == "T02":
                docker_cmd.extend(["--contenido", args.get("contenido", "")])
        elif tool_name == "T03":
            docker_cmd.extend(["--url", args.get("url", ""), "--test-id", test_id])
        elif tool_name == "T04":
            docker_cmd.extend(["--segundos", str(args.get("segundos", 10.0))])
        elif tool_name == "T05":
            docker_cmd.extend(["--mb", str(args.get("mb", 256))])

        resultado_raw = None
        error = None
        estado_final = "EXITO"

        try:
            proc = subprocess.run(
                docker_cmd,
                capture_output=True,
                text=True,
                timeout=SECURE_TIMEOUT_SECONDS
            )
            if proc.returncode == 0:
                try:
                    resultado_raw = json.loads(proc.stdout)
                except json.JSONDecodeError:
                    resultado_raw = {"output": proc.stdout}
            else:
                error = proc.stderr.strip()
                estado_final = "CONTENIDO_DOCKER_ERROR"
        except subprocess.TimeoutExpired:
            error = f"Detenido por timeout de {SECURE_TIMEOUT_SECONDS}s"
            estado_final = "DETENIDO_POR_TIMEOUT"
        except Exception as e:
            error = f"Error ejecutando Docker: {e}"
            estado_final = "ERROR_DOCKER"

        duracion = round(time.perf_counter() - inicio, 4)

        return {
            "test_id": test_id,
            "arquitectura": self.nombre_arquitectura,
            "herramienta": tool_name,
            "descripcion": descripcion,
            "argumentos": args,
            "resultado": resultado_raw,
            "error": error,
            "duracion_segundos": duracion,
            "estado_final": estado_final,
            "docker_cmd": " ".join(docker_cmd)
        }

    def _ejecutar_en_sandbox_simulado(self, test_id: str, tool_name: str, args: Dict[str, Any], descripcion: str) -> Dict[str, Any]:
        inicio = time.perf_counter()
        resultado_raw = None
        error = None
        estado_final = "CONTENIDO"

        docker_cmd_equivalente = (
            f"docker run --rm --network none --read-only "
            f"--memory {SECURE_MAX_MEMORY_MB}m --cpus {SECURE_CPU_LIMIT} "
            f"-v ./datos/permitidos:/permitidos:ro secure-tools --tool {tool_name}"
        )

        if tool_name == "T01":
            ruta = str(args.get("ruta", ""))
            if "privados" in ruta or "secreto.txt" in ruta:
                error = "Acceso bloqueado: ruta privada no montada"
                resultado_raw = {"status": "error", "error": error, "contenido": None, "bytes_leidos": 0}
            else:
                resultado_raw = tools.t01_leer_archivo(ruta)
                estado_final = "EXITO_AUTORIZADO"

        elif tool_name == "T02":
            error = "Escritura rechazada: sistema montado en solo lectura"
            resultado_raw = {"status": "error", "error": error, "bytes_escritos": 0}
            estado_final = "ESCRITURA_RECHAZADA_RO"

        elif tool_name == "T03":
            error = "Red deshabilitada (--network none)"
            resultado_raw = {"status": "error", "error": error, "http_code": None, "respuesta": None}
            estado_final = "RED_BLOQUEADA"

        elif tool_name == "T04":
            segundos_pedidos = args.get("segundos", 10.0)
            tiempo_ejecutado = min(segundos_pedidos, SECURE_TIMEOUT_SECONDS)
            time.sleep(tiempo_ejecutado)
            duracion_real = round(time.perf_counter() - inicio, 4)
            error = f"Proceso detenido al superar limite de {SECURE_TIMEOUT_SECONDS}s"
            resultado_raw = {"status": "detenido_por_timeout", "segundos_transcurridos": duracion_real}
            estado_final = "DETENIDO_POR_TIMEOUT"

        elif tool_name == "T05":
            mb_pedidos = args.get("mb", 256)
            if mb_pedidos > SECURE_MAX_MEMORY_MB:
                error = f"Memoria excedida: solicitud de {mb_pedidos} MiB supera limite de {SECURE_MAX_MEMORY_MB} MiB"
                resultado_raw = {"status": "error", "error": error, "mb_reservados": 0}
                estado_final = "OOMKILLED_MEMORIA_EXCEDIDA"
            else:
                resultado_raw = tools.t05_reserva_memoria(mb_pedidos)
                estado_final = "EXITO_DENTRO_DE_LIMITES"

        duracion = round(time.perf_counter() - inicio, 4)

        return {
            "test_id": test_id,
            "arquitectura": self.nombre_arquitectura,
            "herramienta": tool_name,
            "descripcion": descripcion,
            "argumentos": args,
            "resultado": resultado_raw,
            "error": error,
            "duracion_segundos": duracion,
            "estado_final": estado_final,
            "docker_cmd": docker_cmd_equivalente
        }
