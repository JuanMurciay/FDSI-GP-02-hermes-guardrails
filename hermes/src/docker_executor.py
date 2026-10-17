"""Ejecución de la lectura permitida en un contenedor efímero y restringido.

La política se aplica antes de llegar aquí. El contenedor añade una segunda barrera:
solo recibe la carpeta permitida, en modo lectura, y carece de red.
"""

from __future__ import annotations

import subprocess
import uuid
from pathlib import Path


IMAGE = "python:3.12-alpine"
READ_SCRIPT = (
    "from pathlib import Path; import sys; "
    "name=sys.argv[1]; "
    "assert name in ('nota.txt', 'ticket.txt'); "
    "print((Path('/lab/permitidos')/name).read_text(encoding='utf-8'), end='')"
)


class SandboxError(RuntimeError):
    pass


def read_allowed(data_dir: Path, filename: str, *, timeout: int = 8) -> str:
    """Lee un archivo permitido con límites del kernel; falla cerrado."""
    if filename not in {"nota.txt", "ticket.txt"}:
        raise SandboxError("Archivo no incluido en la lista permitida")
    source = (data_dir / "permitidos").resolve()
    if not (source / filename).is_file():
        raise SandboxError("Archivo permitido inexistente")
    name = "fdsi-tool-" + uuid.uuid4().hex[:12]
    command = [
        "docker", "run", "--rm", "--name", name, "--network", "none", "--read-only",
        "--memory", "128m", "--memory-swap", "128m", "--cpus", "0.5",
        "--pids-limit", "64", "--cap-drop", "ALL",
        "--security-opt", "no-new-privileges", "--user", "65534:65534",
        "--mount", f"type=bind,source={source},target=/lab/permitidos,readonly",
        IMAGE, "python", "-c", READ_SCRIPT, filename,
    ]
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=timeout, check=False)
    except subprocess.TimeoutExpired as error:
        try:
            subprocess.run(["docker", "rm", "-f", name], capture_output=True, timeout=5, check=False)
        except (OSError, subprocess.TimeoutExpired):
            pass
        raise SandboxError("Contenedor excedió el tiempo permitido") from error
    except OSError as error:
        raise SandboxError(f"Contenedor no disponible: {type(error).__name__}") from error
    if result.returncode != 0:
        raise SandboxError(f"Lectura aislada falló (código {result.returncode})")
    return result.stdout
