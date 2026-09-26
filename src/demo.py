"""Demo As-Is / To-Be sin modelo ni cuentas externas."""

from pathlib import Path
from tempfile import TemporaryDirectory
from shutil import copytree

from supervisor import Supervisor
from servidor_local import Handler
from http.server import ThreadingHTTPServer
from threading import Thread


ROOT = Path(__file__).resolve().parents[1]


def main():
    with TemporaryDirectory(prefix="fdsi_demo_") as temporary:
        data = Path(temporary) / "datos"
        copytree(ROOT / "datos", data)
        log = ROOT / "evidencias" / "demo.jsonl"
        supervisor = Supervisor(data, log)
        server = ThreadingHTTPServer(("127.0.0.1", 8765), Handler)
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            cases = [
                ("D01", "read_file", "permitidos/nota.txt"),
                ("D02", "read_file", "privados/secreto.txt"),
                ("D03", "write_file", "permitidos/nota.txt"),
                ("D04", "http_get", "http://127.0.0.1:8765/prueba"),
                ("D05", "read_file", "../fuera.txt"),
            ]
            print("ID   Acción       AS-IS       TO-BE       Riesgo")
            print("-" * 67)
            risks = {
                "D01": "función legítima",
                "D02": "confidencialidad",
                "D03": "integridad",
                "D04": "salida de red",
                "D05": "salida del laboratorio",
            }
            for test_id, action, target in cases:
                outcomes = []
                for mode in ("as-is", "to-be"):
                    response = supervisor.execute(mode, action, target, "cambio ficticio")
                    outcomes.append("PERMITE" if response["audit"]["allowed"] else "BLOQUEA")
                print(f"{test_id}  {action:<12} {outcomes[0]:<11} {outcomes[1]:<11} {risks[test_id]}")
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)
    print(f"Registro: {log}")
    print("Nota: tiempo, memoria y CPU requieren controles del sistema operativo; pendientes.")


if __name__ == "__main__":
    main()
