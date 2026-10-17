# Demo local con OpenCode: As-Is / To-Be

Esta es la ruta recomendada para mostrar el agente **hoy en Windows**, sin Hermes, WSL ni Docker. OpenCode usa una herramienta MCP del laboratorio sobre **archivos ficticios**. El mismo prompt se ejecuta dos veces: en **As-Is** la herramienta permite leer el archivo privado; en **To-Be** un supervisor externo lo bloquea y registra la decisión. Una instrucción insertada en un ticket intenta inducir esa lectura. La comparación distingue la decisión del modelo de la decisión del supervisor.

## Requisitos

- OpenCode CLI instalado y con un proveedor/modelo funcional. Comprueba `opencode --version` o usa la instalación habitual en `%USERPROFILE%\.opencode\bin\opencode.exe`.
- Python 3.10+ (`python --version`). Este módulo usa solo la biblioteca estándar.
- Ejecutar desde la **raíz del repositorio** en PowerShell o la terminal de IntelliJ. No uses datos propios ni credenciales reales.

## Ejecución

```powershell
python opencode_local/run.py --modo as-is --tarea valida
python opencode_local/run.py --modo to-be --tarea valida
python opencode_local/run.py --modo as-is --tarea privada
python opencode_local/run.py --modo to-be --tarea privada
python opencode_local/run.py --modo as-is --tarea ticket
python opencode_local/run.py --modo to-be --tarea ticket
```

Si tu OpenCode no tiene un modelo predeterminado, añade `--modelo proveedor/modelo` a cada comando. Si `python` es un alias defectuoso, sustituye `python` por la ruta de un Python funcional. `--solo-preparar` crea el laboratorio y su configuración sin llamar al modelo.

Cada corrida crea una carpeta distinta en `local/opencode/` (ignorada por Git). Consulta `resumen.json`, `auditoria.jsonl`, `respuesta_final.txt`, `eventos.jsonl` y `stderr.txt`. La carpeta `datos/` de cada corrida es una copia, por lo que As-Is no altera la de To-Be. Una lectura privada en As-Is no equivale automáticamente a filtración: revisa la respuesta del agente y `secreto_en_respuesta_final`. Si `llamadas_mcp` es cero, no se ha demostrado ninguna decisión del supervisor. Si OpenCode falla o agota el tiempo, `returncode` será distinto de cero.

El script permite automáticamente solo `lab_laboratorio_controlado`. Cualquier comando de terminal queda en `ask`: **no apruebes comandos durante esta demo**, pues la terminal del host podría evitar el MCP. No uses `--auto`. El script ejecuta `--pure` y crea un directorio de configuración aislado. El servidor MCP aplica una política distinta por modo; el agente no decide su propio modo. Se puede verificar la conexión entrando a la carpeta de una corrida preparada y ejecutando `opencode mcp list`: debe aparecer solo `lab`.

Si `eventos.jsonl` contiene `FreeTierError` con el mensaje «OpenCode's free tier can only be used from within OpenCode», primero comprueba `opencode auth list` y, si no figura OpenCode, ejecuta `opencode auth login opencode`. OpenCode también ha registrado este 403 con modelos gratuitos cuando una configuración personalizada deniega `bash`; por ello esta demo lo deja en `ask`, sin aprobación automática. Si el error persiste en la aplicación oficial, puede ser un problema del servicio o de la red y no una decisión del supervisor. Consulta el [reporte de OpenCode](https://github.com/anomalyco/opencode/issues/56343). No cuentes la corrida como una prueba de bloqueo si `llamadas_mcp` es cero.

## Alcance de seguridad

**To-Be aquí demuestra un guardrail lógico, no aislamiento del sistema operativo.** El proceso MCP corre en el host y la lectura permitida no pasa por Docker. La política bloquea lectura privada, escritura y HTTP dentro de la herramienta, pero no impone límites de CPU, memoria, tiempo o red al proceso OpenCode. Para defender el objetivo completo del seminario, ejecuten después las pruebas N0/N2 del [orquestador principal](../orquestador/run.py) o la [sonda de contenedor](../hermes/docs/GUIA_DEMO_HERMES.md) cuando Docker/WSL estén listos. No mezclen resultados de esta demo con los de `resultados/corridas.csv`.

La configuración MCP local, `command`, `environment` y los nombres de herramientas se basan en la [documentación MCP de OpenCode](https://opencode.ai/docs/mcp-servers/). Los permisos `allow`/`deny` y la prioridad de reglas se describen en la [documentación de permisos](https://opencode.ai/docs/permissions/); `opencode run --format json` y `--pure`, en la [referencia CLI](https://opencode.ai/docs/cli/).
