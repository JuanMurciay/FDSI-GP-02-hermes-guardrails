# Estado verificable al 17 de octubre de 2026

## Implementado en el repositorio

- Laboratorio con archivos ficticios y ticket con una instrucción de tercero.
- Supervisor de aplicación As-Is/To-Be, auditoría JSONL y demo local determinista.
- Servidor MCP por `stdio` y prueba de intercambio real con un cliente JSON-RPC.
- Perfiles locales generables para Hermes, separados por modo y con un único toolset MCP propuesto. No se guardan claves en Git.
- Copias independientes de los datos por modo, para que As-Is no cambie los archivos del repositorio.
- Ejecutor Docker en To-Be para la lectura legítima, con montaje `readonly`, red `none`, raíz de solo lectura y límites de CPU, memoria, procesos y tiempo.
- Sondas de Docker para probar las barreras de archivos, escritura, red, tiempo y memoria por separado.
- Modelo de amenazas, guion de la demo, criterios de medición y referencias primarias.
- 13 pruebas automáticas de política, MCP y construcción del contenedor superadas en este equipo.

## Aún sin comprobar en una ejecución completa

- La instalación local de Hermes anuncia versión `v0.21.5+2504.ga0fe806`, pero `hermes chat --help` termina con `ModuleNotFoundError: ruamel`. Hay que reparar la instalación antes de conectarlo al MCP.
- Docker Desktop está instalado, pero `docker info` no conecta al motor Linux. Las sondas de contenedor y la lectura To-Be con Docker no se han podido ejecutar aquí.
- No se ha verificado la lista de herramientas que Hermes muestra en `/tools` con estos perfiles. Si aparece una vía alternativa, la prueba no cumple el modelo de amenazas.
- No hay resultados medidos de llamadas de Hermes, repeticiones, latencias, éxito de tarea legítima ni inyección de prompt. Las tablas de la guía contienen expectativas, no resultados.

## Siguiente verificación

Reparar Hermes y arrancar Docker; ejecutar los comandos de [GUIA_DEMO_HERMES.md](GUIA_DEMO_HERMES.md), conservar logs/transcripciones y repetir cinco veces por condición. Solo después se podrá redactar una conclusión experimental.
