"""Resume decisiones MCP observadas; no inventa intentos que el agente no realizó."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def summarize(files: list[Path]) -> list[dict]:
    counts: Counter[tuple[str, str, str, bool]] = Counter()
    for path in files:
        if not path.is_file():
            continue
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            try:
                item = json.loads(line)
                key = (item["mode"], item["action"], item["target"], bool(item["allowed"]))
            except (ValueError, KeyError, TypeError) as error:
                raise SystemExit(f"Registro inválido {path}:{number}: {error}") from error
            counts[key] += 1
    return [{"modo": mode, "accion": action, "objetivo": target,
             "permitido": allowed, "cantidad": count}
            for (mode, action, target, allowed), count in sorted(counts.items())]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("logs", nargs="*", type=Path, default=[
        ROOT / "evidencias" / "hermes-as-is.jsonl",
        ROOT / "evidencias" / "hermes-to-be.jsonl",
    ])
    args = parser.parse_args()
    rows = summarize(args.logs)
    if not rows:
        raise SystemExit("No hay llamadas registradas; no se pueden calcular métricas")
    output = ROOT / "evidencias" / "resumen.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["modo", "accion", "objetivo", "permitido", "cantidad"])
        writer.writeheader()
        writer.writerows(rows)
    for row in rows:
        print(row)
    print(f"Resumen: {output}")


if __name__ == "__main__":
    main()
