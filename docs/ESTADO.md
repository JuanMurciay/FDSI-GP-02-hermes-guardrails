# Estado verificable de esta entrega

## Implementado

- Datos ficticios en carpetas `permitidos` y `privados`.
- Supervisor externo en Python con política As-Is/To-Be para lectura, escritura y HTTP local.
- Registro JSONL de decisiones del supervisor.
- Demo automática que muestra ambas políticas con las mismas solicitudes.
- Adaptador MCP por stdio para que, en una fase siguiente, Hermes invoque la herramienta supervisada.
- Pruebas automáticas locales del supervisor y del protocolo inicial del adaptador.
- Investigación con riesgos de confidencialidad, integridad, disponibilidad y elusión del supervisor.

## Pendiente

- Instalar/configurar Hermes Agent con un proveedor de modelo y probar la llamada real al MCP.
- Quitar rutas alternas de acceso desde Hermes y separar procesos/identidades.
- Aplicar controles Docker de archivos, red, tiempo, memoria y CPU a la herramienta real.
- Ejecutar T01-T05 cinco veces en cada arquitectura y guardar métricas.
- Completar análisis, video, paper IEEE y presentación final.

La tabla D01-D05 de la demo local es evidencia del **supervisor de aplicación**. No demuestra todavía el aislamiento de Docker ni la seguridad completa de Hermes. El objetivo de la siguiente entrega es cerrar esa diferencia.
