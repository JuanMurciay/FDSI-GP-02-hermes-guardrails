# Investigación inicial: riesgo y controles

## Problema y activo

Un agente con acceso a herramientas puede producir efectos fuera de la conversación: leer archivos, escribirlos o llamar servicios. Los activos del experimento son la **confidencialidad** del archivo privado ficticio, la **integridad** del archivo autorizado y la **disponibilidad** del entorno. OWASP llama *Excessive Agency* al riesgo creado por funciones, permisos o autonomía mayores a los necesarios [1]. No es necesario que el modelo sea malicioso: una instrucción ambigua, una inyección de prompt o una herramienta comprometida puede llevarlo a usar capacidades válidas de manera peligrosa [1][2].

## Tipos de riesgo que mediremos

| Riesgo | Ejemplo en el laboratorio | Impacto | Control propuesto | Evidencia |
| --- | --- | --- | --- | --- |
| Confidencialidad / permisos excesivos | La herramienta lee `privados/secreto.txt`. | Revelación de datos. | Política externa y carpeta privada no montada en To-Be. | Resultado de lectura y registro de denegación. |
| Integridad / modificación no autorizada | La herramienta cambia `permitidos/nota.txt`. | Alteración de información. | Herramienta de solo lectura y montaje `ro`. | Hash antes y después. |
| Red / posible exfiltración | La herramienta solicita una URL. | Comunicación no autorizada. | Denegación en política y red `none` en contenedor. | Registro del servidor y decisión del supervisor. |
| Disponibilidad / agotamiento | La herramienta tarda demasiado o consume memoria/CPU. | Degradación del servicio. | Tiempo máximo y límites de recursos del contenedor. | Duración, estado y consumo. |
| Elusión de guardrails | El agente usa otra herramienta para saltarse el supervisor. | Todos los impactos anteriores. | Quitar vías alternas, aislar Hermes y separar identidad/proceso del supervisor. | Inventario de herramientas y prueba de acceso directo denegado. |

La inyección de prompt se considera **causa posible** de una solicitud indebida, mientras que el permiso excesivo determina el daño que esa solicitud podría causar. OWASP separa el problema de la instrucción manipulada del de la autonomía y permisos de las herramientas [1][2]. En la primera demo usaremos solicitudes predeterminadas; no diremos que probamos ataques de prompt injection hasta tener Hermes configurado.

## Fuentes técnicas consultadas

1. **OWASP LLM06: Excessive Agency**: propone limitar funciones, permisos y autonomía; también recomienda registrar la actividad [1]. Por eso el To-Be tiene una sola lectura permitida y deja evidencia de cada decisión.
2. **OWASP LLM01: Prompt Injection**: explica cómo instrucciones dentro de contenido no confiable pueden alterar el comportamiento del modelo [2]. Esto justifica separar la decisión de autorización del texto que lee el agente.
3. **Hermes Agent, configuración y seguridad**: documenta backends de terminal local y Docker, aprobaciones, toolsets y filtrado de credenciales [3][4]. Su backend Docker reduce la exposición de comandos, pero hay que revisar montajes y herramientas disponibles; una aprobación del agente no sustituye controles externos.
4. **NIST SP 800-190**: los contenedores ayudan a separar aplicaciones, pero necesitan configuración de seguridad y supervisión [5]. Esto respalda comprobar el aislamiento real en vez de darlo por hecho.
5. **Docker, bind mounts**: los montajes son de escritura por defecto y admiten `readonly` [6]. En To-Be la carpeta autorizada se montará solo para lectura.
6. **Docker, red none y límites de recursos**: la red `none` elimina la interfaz externa del contenedor; Docker permite limitar memoria y CPU [7][8]. El tiempo máximo lo controlará el ejecutor externo.

## Decisión de diseño

El supervisor acepta una solicitud estructurada `{action, target, content}`, evalúa una política fijada por el operador y devuelve resultado y motivo. El agente no elige el modo As-Is/To-Be en la herramienta MCP. Esta separación impide que un simple argumento cambie la política. Aun así, el supervisor en Python es **un control de aplicación**: para resistir acceso directo desde un agente con shell, la siguiente fase debe aislar procesos y archivos mediante el sistema operativo y Docker.

Todas las referencias completas están en [REFERENCIAS.md](REFERENCIAS.md).
