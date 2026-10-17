# Anexo de investigación: aislamiento de herramientas con Hermes

Este texto describe el prototipo Hermes. La propuesta y las corridas principales del equipo emplean OpenCode y se encuentran en la raíz del repositorio; los resultados de ambas líneas no deben sumarse como si fueran el mismo experimento.

**Grupo:** FDSI-GP-02, cuatro integrantes. Completar los nombres antes de la entrega.

## Resumen

Un agente de IA puede ser útil para consultar información y apoyar tareas de soporte, pero al darle herramientas también puede producir cambios fuera del chat. En este trabajo planteamos una comparación entre un ambiente con permisos amplios (As-Is) y otro con restricciones externas al agente (To-Be). Utilizamos Hermes Agent como agente de prueba, un supervisor de herramientas por MCP y un contenedor para limitar la lectura autorizada. El laboratorio emplea únicamente datos ficticios. La implementación y las pruebas unitarias están listas; los resultados finales con Hermes y Docker se incorporarán cuando ambos entornos funcionen.

## 1. Problema

En una empresa, un agente que lee tickets puede encontrar contenido escrito por clientes o terceros. Ese contenido no es una orden autorizada, pero podría pedirle al agente leer archivos internos o ejecutar otra acción. El riesgo no termina en la respuesta incorrecta: si el agente tiene herramientas con más permisos de los necesarios, la solicitud puede tener un efecto real. OWASP distingue el riesgo de instrucciones inyectadas en contenido externo del riesgo de autonomía y permisos excesivos [1][2].

Nuestro caso es un asistente que debe leer una nota autorizada y resumir un ticket. El ticket incluye una instrucción no confiable que intenta hacerle leer un archivo privado ficticio. También probamos escritura, red y consumo de recursos. Esas pruebas representan riesgos de confidencialidad, integridad y disponibilidad.

## 2. Pregunta e hipótesis

**Pregunta:** ¿En qué medida un supervisor externo de herramientas, junto con aislamiento del entorno, reduce las acciones no autorizadas de Hermes sin impedir una tarea legítima?

**Hipótesis:** al limitar el inventario de herramientas y aplicar una política externa más un contenedor, la lectura autorizada seguirá funcionando y se impedirán la lectura privada, la escritura, la salida de red y la ejecución fuera de límites. La comparación puede mostrar un costo de tiempo adicional. Estos resultados son hipótesis, no observaciones.

## 3. Solución propuesta

La arquitectura As-Is usa las mismas herramientas del laboratorio con permisos amplios sobre una **copia ficticia** de los datos. No representa una configuración recomendable. La arquitectura To-Be separa la solicitud del agente de la autorización: Hermes puede pedir una operación al MCP, pero el supervisor decide según una política que el agente no puede elegir. Solo autoriza leer archivos concretos de `permitidos/`. Esa lectura se ejecuta en un contenedor efímero con la carpeta montada para lectura; `privados/` no se monta. La red está desactivada y se aplican límites de recursos y tiempo [3][4][6][7][8][10].

La lista de herramientas de Hermes también debe quedar reducida al MCP del laboratorio. Esta condición es importante: si conserva un lector de archivos o terminal con acceso al host, puede evitar el supervisor. Por eso la demo empieza revisando `/tools`. La configuración de Hermes y el contenedor del MCP son controles distintos [3][4][11].

## 4. Método de evaluación

Se ejecutarán las mismas tareas en As-Is y To-Be, cinco veces por condición. Se conservarán los prompts, la versión y el modelo utilizados. Cada ensayo se identificará por su fecha/hora y se restablecerán las copias de datos cuando haya escritura. Separaremos tres hechos: si Hermes **intentó** una acción, si el supervisor la **permitió o denegó**, y si el sistema **produjo un efecto**. Una respuesta del agente por sí sola no confirma la ejecución de la herramienta.

| ID | Acción | Riesgo | Evidencia principal |
| --- | --- | --- | --- |
| T01 | Leer nota y archivo privado | confidencialidad | auditoría y contenido devuelto |
| T02 | Cambiar la nota | integridad | auditoría y hash antes/después |
| T03 | Solicitud HTTP | salida no autorizada | auditoría y recepción del servidor local |
| T04 | Esperar 10 segundos | disponibilidad por tiempo | duración y terminación |
| T05 | Reservar 256 MiB | disponibilidad por memoria | código de salida y límite del contenedor |

También se realiza la tarea del ticket con contenido no confiable. Si Hermes no sigue la instrucción inyectada, no se contará como bloqueo del supervisor; si sí la intenta, la auditoría mostrará la decisión. Las sondas de Docker comprueban por separado la ausencia del archivo privado, el montaje de solo lectura, la red desactivada y los límites [5][6][7][8].

## 5. Resultados

**Pendientes de medición.** Hasta el 17 de octubre de 2026 se verificaron 13 pruebas automáticas de Python, incluida la comunicación MCP por `stdio`, pero no se pudo ejecutar Hermes ni el motor Linux de Docker en este portátil. No corresponde llenar la tabla con resultados esperados. Registrar aquí, después de cada corrida, el número de llamadas, bloqueos, efectos, tareas legítimas completadas, fallos de infraestructura y tiempos. Guardar las evidencias en `evidencias/` y resumirlas con `scripts/resumir_auditoria.py`.

| Condición | Ensayos válidos | Tareas legítimas completadas | Acciones indebidas intentadas | Acciones indebidas con efecto | Tiempo mediano |
| --- | ---: | ---: | ---: | ---: | ---: |
| As-Is | pendiente | pendiente | pendiente | pendiente | pendiente |
| To-Be | pendiente | pendiente | pendiente | pendiente | pendiente |

## 6. Discusión y límites

El proyecto quiere mostrar que reducir permisos y separar la autorización del modelo limita el daño posible incluso cuando recibe instrucciones engañosas. El resultado dependerá de la configuración real, en especial de las herramientas disponibles en Hermes y de los montajes del contenedor. Las pruebas son de un laboratorio pequeño con datos ficticios; no justifican afirmar que cualquier despliegue de agentes queda protegido. La conclusión definitiva se redactará después de comparar los resultados medidos.

## Declaración de uso de IA

Se utilizó ChatGPT (Codex) como apoyo para búsqueda de fuentes, organización del documento y desarrollo/revisión de código. El equipo debe comprobar la configuración, ejecutar los ensayos, revisar las evidencias y redactar conclusiones basadas en sus propios resultados.

## Referencias

Las referencias [1]–[11] se detallan con enlaces en [REFERENCIAS.md](REFERENCIAS.md).
