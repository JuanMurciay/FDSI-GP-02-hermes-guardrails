"""Pruebas técnicas del contenedor, independientes de las respuestas del modelo.

Requiere Docker Desktop con motor Linux y la imagen python:3.12-alpine.
Guarda resultados medidos; nunca sustituye fallos por éxitos esperados.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = (ROOT / "datos").resolve()
IMAGE = "python:3.12-alpine"


def container_run(code: str, *, secure: bool, data_dir: Path, timeout: int = 8) -> dict:
    name = "fdsi-probe-" + uuid.uuid4().hex[:12]
    memory = "128m" if secure else "512m"
    cpu = "0.5" if secure else "1"
    flags = ["--rm", "--name", name, "--memory", memory, "--memory-swap", memory,
             "--cpus", cpu, "--pids-limit", "64", "--cap-drop", "ALL",
             "--security-opt", "no-new-privileges"]
    if secure:
        flags += ["--network", "none", "--read-only", "--user", "65534:65534",
                  "--mount", f"type=bind,source={data_dir / 'permitidos'},target=/lab/permitidos,readonly"]
    else:
        # As-Is queda igualmente confinado al directorio ficticio del laboratorio.
        flags += ["--mount", f"type=bind,source={data_dir},target=/lab"]
    command = ["docker", "run", *flags, IMAGE, "python", "-c", code]
    start = time.monotonic()
    try:
        result = subprocess.run(command, text=True, capture_output=True, timeout=timeout)
        return {"exit_code": result.returncode, "stdout": result.stdout.strip(),
                "stderr_tail": result.stderr.strip()[-300:], "seconds": round(time.monotonic() - start, 3),
                "timeout": False}
    except subprocess.TimeoutExpired:
        # Matar el cliente docker no garantiza detener el contenedor del daemon.
        try:
            subprocess.run(["docker", "rm", "-f", name], capture_output=True, timeout=5)
        except (OSError, subprocess.TimeoutExpired):
            pass
        return {"exit_code": None, "stdout": "", "stderr_tail": "", "seconds": round(time.monotonic() - start, 3),
                "timeout": True}


def main() -> int:
    probe = subprocess.run(["docker", "info", "--format", "{{.ServerVersion}}"],
                           capture_output=True, text=True)
    if probe.returncode != 0:
        print("Docker Linux no está disponible; ninguna prueba se marcó como realizada.", file=sys.stderr)
        return 2
    cases = {
        "archivo_permitido": "from pathlib import Path; print(Path('/lab/permitidos/nota.txt').read_text())",
        "archivo_privado": "from pathlib import Path; print(Path('/lab/privados/secreto.txt').read_text())",
        "escritura": "from pathlib import Path; Path('/lab/permitidos/nota.txt').write_text('CAMBIO_DE_PRUEBA'); print('escrito')",
        "red": "import socket; socket.create_connection(('1.1.1.1',80), timeout=2); print('conectado')",
        "tiempo": "import time; time.sleep(10); print('terminado')",
        "memoria": "x=bytearray(256*1024*1024); print(len(x))",
    }
    report = {"timestamp_utc": datetime.now(timezone.utc).isoformat(),
              "docker_version": probe.stdout.strip(), "image": IMAGE, "results": {}}
    scratch = ROOT / "local" / "test-tmp"
    scratch.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=scratch) as temporary:
        copied = Path(temporary) / "datos"
        shutil.copytree(DATA, copied)
        for mode in ("as-is", "to-be"):
            for case, code in cases.items():
                # La prueba de red abierta en As-Is no es necesaria: el servidor local
                # de la demo básica ya registra esa capacidad sin tráfico a terceros.
                if mode == "as-is" and case == "red":
                    continue
                case_timeout = (2 if mode == "to-be" else 12) if case == "tiempo" else 8
                result = container_run(code, secure=(mode == "to-be"), data_dir=copied,
                                       timeout=case_timeout)
                report["results"][f"{mode}/{case}"] = result
                print(f"{mode:5} {case:18} exit={result['exit_code']} timeout={result['timeout']}")
    output = ROOT / "evidencias" / "contenedor.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Evidencia: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
