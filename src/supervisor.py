"""Control externo de las herramientas del laboratorio. Solo usa datos ficticios."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import urlopen


class Supervisor:
    def __init__(self, data_dir: Path, audit_file: Path | None = None):
        self.data_dir = data_dir.resolve()
        self.audit_file = audit_file

    def _audit(self, mode: str, action: str, target: str, allowed: bool, reason: str):
        record = {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "mode": mode,
            "action": action,
            "target": target,
            "allowed": allowed,
            "reason": reason,
        }
        if self.audit_file:
            self.audit_file.parent.mkdir(parents=True, exist_ok=True)
            with self.audit_file.open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(record, ensure_ascii=False) + "\n")
        return record

    def execute(self, mode: str, action: str, target: str, content: str = "") -> dict:
        if mode not in {"as-is", "to-be"}:
            raise ValueError("Modo desconocido")
        if action not in {"read_file", "write_file", "http_get"}:
            raise ValueError("Herramienta no reconocida")
        try:
            if action in {"read_file", "write_file"}:
                path = (self.data_dir / target).resolve()
                if self.data_dir not in path.parents:
                    record = self._audit(mode, action, target, False, "Ruta fuera del laboratorio")
                    return {"audit": record, "result": None}
                if not path.is_file():
                    record = self._audit(mode, action, target, False, "Archivo inexistente")
                    return {"audit": record, "result": None}
                if mode == "to-be" and not (
                    action == "read_file" and path.parent == self.data_dir / "permitidos"
                ):
                    record = self._audit(mode, action, target, False, "Política de mínimo privilegio")
                    return {"audit": record, "result": None}
                if action == "read_file":
                    result = path.read_text(encoding="utf-8")
                else:
                    path.write_text(content, encoding="utf-8")
                    result = "Archivo modificado"
            else:
                parsed = urlparse(target)
                if mode == "to-be":
                    record = self._audit(mode, action, target, False, "Red no autorizada")
                    return {"audit": record, "result": None}
                if parsed.scheme != "http" or parsed.hostname != "127.0.0.1" or parsed.port != 8765 or parsed.path != "/prueba":
                    record = self._audit(mode, action, target, False, "Solo se admite servidor local de prueba")
                    return {"audit": record, "result": None}
                with urlopen(target, timeout=2) as response:
                    result = response.read().decode("utf-8")
            record = self._audit(mode, action, target, True, "Permitido por política")
            return {"audit": record, "result": result}
        except (OSError, ValueError) as error:
            record = self._audit(mode, action, target, False, f"Error de ejecución: {type(error).__name__}")
            return {"audit": record, "result": None}
