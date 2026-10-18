# Hermes y el supervisor externo

Hermes es el agente que se utilizará para estudiar el uso de herramientas. El servidor MCP `src/mcp_guardrail.py` expone `laboratorio_controlado`; el modo y las rutas de datos se fijan en el proceso del servidor, no en los argumentos que envía el modelo [10].

`scripts/preparar_hermes.py` crea perfiles locales As-Is y To-Be. Cada perfil lista únicamente `mcp-laboratorio`, según el mecanismo de toolsets dinámicos de Hermes [11]. En To-Be, la lectura que el supervisor autoriza se ejecuta en un contenedor efímero; las demás acciones se deniegan sin llegar a Docker. Las copias de datos y los perfiles quedan ignorados por Git.

El perfil también configura el backend Docker de Hermes como defensa adicional, pero la herramienta MCP corre como proceso propio en el host y usa su **propio** contenedor para la lectura. Configurar el backend Docker de Hermes por sí solo no aislaría automáticamente un servidor MCP que corre fuera de él. La revisión de `/tools` es indispensable: un shell, lector de archivos, ejecutor de código u otro MCP con acceso al host invalidaría el resultado de aislamiento [3][4][11].

La [guía paso a paso](GUIA_DEMO_HERMES.md) cubre preparación, prompts, evidencia y fallos conocidos. La instalación de Hermes y Docker en este portátil aún impiden ejecutar la sesión final; véase [ESTADO.md](ESTADO.md).
