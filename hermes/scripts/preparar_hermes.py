"""Genera perfiles locales de Hermes sin copiar credenciales ni tocar la config personal."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def create_profiles(python_exe: Path) -> None:
    server = (ROOT / "src" / "mcp_guardrail.py").resolve()
    if not python_exe.is_file():
        raise SystemExit(f"Python no existe: {python_exe}")
    for mode in ("as-is", "to-be"):
        folder = ROOT / "local" / f"hermes-{mode}"
        folder.mkdir(parents=True, exist_ok=True)
        fixture = ROOT / "local" / "fixtures" / mode / "datos"
        fixture_root = (ROOT / "local" / "fixtures").resolve()
        if not fixture.resolve().is_relative_to(fixture_root):
            raise SystemExit("Ruta de fixture fuera del laboratorio")
        fixture.parent.mkdir(parents=True, exist_ok=True)
        if fixture.exists():
            shutil.rmtree(fixture)
        shutil.copytree(ROOT / "datos", fixture)
        audit_file = ROOT / "evidencias" / f"hermes-{mode}.jsonl"
        # JSON strings son escalares YAML válidos; evita errores por barras de Windows.
        import json
        config = "\n".join([
            "# Perfil exclusivo del laboratorio FDSI-GP-02. No guardar claves aquí.",
            "toolsets:",
            "  - mcp-laboratorio",
            "terminal:",
            "  backend: docker",
            "  docker_network: false",
            "  docker_mount_cwd_to_workspace: false",
            "  docker_forward_env: []",
            "  container_cpu: 0.5",
            "  container_memory: 128",
            "mcp_servers:",
            "  laboratorio:",
            f"    command: {json.dumps(str(python_exe.resolve()))}",
            f"    args: [{json.dumps(str(server))}]",
            "    env:",
            f"      FDSI_MODE: {json.dumps(mode)}",
            f"      FDSI_DATA_DIR: {json.dumps(str(fixture.resolve()))}",
            f"      FDSI_AUDIT_FILE: {json.dumps(str(audit_file.resolve()))}",
            "    tools:",
            "      include: [laboratorio_controlado]",
            "      resources: false",
            "      prompts: false",
            "",
        ])
        config_file = folder / "config.yaml"
        if not config_file.exists():
            config_file.write_text(config, encoding="utf-8")
    print("Perfiles creados en local/hermes-as-is y local/hermes-to-be")
    print("Configura el proveedor/modelo en cada perfil sin subir claves al repositorio.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--python", type=Path, default=Path(sys.executable))
    create_profiles(parser.parse_args().python)
