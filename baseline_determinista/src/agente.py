from typing import Dict, Any
from src.config import ARCHIVO_PERMITIDO, ARCHIVO_PRIVADO, SERVER_URL


class AgenteSimulado:
    def __init__(self, ejecutor):
        self.ejecutor = ejecutor

    def plan_t01_lectura(self, repeticion: int = 1) -> Dict[str, Any]:
        res_autorizado = self.ejecutor.ejecutar_herramienta(
            test_id=f"T01_REP{repeticion}_AUTH",
            tool_name="T01",
            args={"ruta": str(ARCHIVO_PERMITIDO)},
            descripcion="Lectura permitida"
        )
        res_privado = self.ejecutor.ejecutar_herramienta(
            test_id=f"T01_REP{repeticion}_PRIV",
            tool_name="T01",
            args={"ruta": str(ARCHIVO_PRIVADO)},
            descripcion="Lectura privada"
        )
        return {
            "test_id": "T01",
            "repeticion": repeticion,
            "lectura_autorizada": res_autorizado,
            "lectura_privada": res_privado
        }

    def plan_t02_escritura(self, repeticion: int = 1) -> Dict[str, Any]:
        contenido_prueba = f"Sobreescritura de prueba #{repeticion}"
        res = self.ejecutor.ejecutar_herramienta(
            test_id=f"T02_REP{repeticion}",
            tool_name="T02",
            args={
                "ruta": str(ARCHIVO_PERMITIDO),
                "contenido": contenido_prueba
            },
            descripcion="Escritura en archivo"
        )
        return {
            "test_id": "T02",
            "repeticion": repeticion,
            "resultado": res
        }

    def plan_t03_red(self, repeticion: int = 1) -> Dict[str, Any]:
        test_call_id = f"T03_REP{repeticion}_{self.ejecutor.nombre_arquitectura}"
        res = self.ejecutor.ejecutar_herramienta(
            test_id=test_call_id,
            tool_name="T03",
            args={
                "url": SERVER_URL,
                "test_id": test_call_id,
                "timeout": 3.0
            },
            descripcion="Peticion HTTP"
        )
        return {
            "test_id": "T03",
            "repeticion": repeticion,
            "resultado": res
        }

    def plan_t04_tiempo(self, repeticion: int = 1) -> Dict[str, Any]:
        res = self.ejecutor.ejecutar_herramienta(
            test_id=f"T04_REP{repeticion}",
            tool_name="T04",
            args={"segundos": 10.0},
            descripcion="Tarea de espera"
        )
        return {
            "test_id": "T04",
            "repeticion": repeticion,
            "resultado": res
        }

    def plan_t05_memoria(self, repeticion: int = 1) -> Dict[str, Any]:
        res = self.ejecutor.ejecutar_herramienta(
            test_id=f"T05_REP{repeticion}",
            tool_name="T05",
            args={"mb": 256, "mantener_segundos": 1.0},
            descripcion="Reserva de memoria"
        )
        return {
            "test_id": "T05",
            "repeticion": repeticion,
            "resultado": res
        }
