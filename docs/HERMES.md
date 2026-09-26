# Integración prevista con Hermes Agent

Hermes Agent es el agente real propuesto para la demostración. Su documentación oficial permite elegir un backend de terminal Docker y configurar herramientas externas mediante MCP [3][4].

## Qué existe hoy

`src/mcp_guardrail.py` implementa un servidor MCP mínimo por stdio. Expone una herramienta `laboratorio_controlado` que recibe `action`, `target` y opcionalmente `content`. El servidor usa la clase `Supervisor` y registra cada decisión. La política `to-be` es predeterminada; una ejecución As-Is debe iniciarse por separado con la variable de entorno `FDSI_MODE=as-is` fijada por el operador. No se permite que el agente elija ese modo en los argumentos.

El protocolo del adaptador se verifica con pruebas locales. **Aún no se ha comprobado una llamada desde una instalación real de Hermes**, ni se ha instalado un modelo o configurado una cuenta. La sintaxis exacta de la configuración debe revisarse con la versión de Hermes que use el equipo.

## Configuración de ejemplo, para validar en el entorno del grupo

La documentación de Hermes muestra servidores MCP con `command` y `args` en `~/.hermes/config.yaml` [4]. Una configuración inicial sería:

```yaml
mcp_servers:
  laboratorio:
    command: python
    args: ["/RUTA/DEL/REPO/src/mcp_guardrail.py"]
    env:
      FDSI_MODE: "to-be"
```

Se debe sustituir la ruta absoluta por la del equipo. Las credenciales del proveedor de modelo **nunca** deben añadirse a este repositorio. La documentación de Hermes indica que los procesos MCP reciben un entorno filtrado y solo las variables indicadas explícitamente en `env` se transmiten [4].

## Barreras que faltan para poder decir que está aislado

- Limitar el inventario de herramientas de Hermes: si conserva un shell local con acceso a los mismos archivos, puede omitir el MCP. Hermes permite deshabilitar toolsets; hay que verificar en la versión instalada cuáles herramientas permanecen [3].
- Ejecutar comandos de Hermes en el backend Docker y revisar los montajes. Hermes advierte que el montaje del directorio de trabajo es opcional y que los montajes de escritura tienen efectos en el host [3].
- Mantener política y registro fuera de la zona donde el agente puede escribir. Separar el proceso del supervisor del proceso que controla el agente.
- Para la herramienta ejecutada, usar una carpeta de datos autorizados montada como solo lectura, red `none`, límites de memoria/CPU y un temporizador externo [5][6][7][8].
- Ensayar un intento de acceso directo a la ruta privada o a la red para comprobar que el sistema operativo también lo impide.

Las aprobaciones nativas de Hermes ayudan a supervisar comandos peligrosos, pero el proyecto medirá controles independientes del texto generado por el modelo [4].

Véanse las fuentes completas en [REFERENCIAS.md](REFERENCIAS.md).
