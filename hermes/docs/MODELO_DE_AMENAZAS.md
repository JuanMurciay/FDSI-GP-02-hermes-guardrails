# Modelo de amenazas y propuesta de solución

## Caso empresarial

Un asistente de soporte consulta un ticket ficticio y una nota autorizada para redactar una respuesta. Necesita leer esos archivos, pero no necesita leer archivos privados, escribir en el sistema, acceder a Internet ni ejecutar tareas largas. El ticket es contenido aportado por un tercero: puede contener instrucciones que el agente no debería obedecer [2].

## Activos, límites y adversario

| Elemento | En el laboratorio | En una empresa podría representar |
| --- | --- | --- |
| Dato privado | `privados/secreto.txt` ficticio | datos de clientes, empleados o credenciales |
| Dato operativo | `permitidos/nota.txt` | guía interna o estado del caso |
| Disponibilidad | CPU, memoria y tiempo de contenedor | capacidad de atender otros casos |
| Frontera 1 | texto del ticket → decisión de Hermes | entrada externa no confiable |
| Frontera 2 | Hermes → MCP supervisor | solicitud de acción, no autorización |
| Frontera 3 | supervisor → contenedor/archivos/red | efecto real sobre el sistema |

El adversario controla el texto del ticket; en la prueba directa también formulamos una petición indebida para verificar el control. No suponemos que controle el código del supervisor, el archivo de configuración ni Docker. Si controla esos componentes, este diseño ya no garantiza protección.

## Riesgos y controles

| Riesgo | Ruta de ataque | Control de aplicación | Control del sistema | Cómo comprobarlo |
| --- | --- | --- | --- | --- |
| Exposición de datos | ticket induce lectura privada | lista permitida de lectura | carpeta privada no montada | auditoría MCP y sonda de archivos |
| Alteración | agente pide escribir nota | denegación de escritura | montaje `readonly`, raíz `read-only` | hash y sonda de escritura |
| Salida de red | herramienta intenta HTTP | denegación de `http_get` | `--network none` | log y sonda de conexión |
| Agotamiento | operación tarda o reserva memoria | tiempo máximo externo | 128 MiB, 0,5 CPU, 64 procesos | duración, salida del contenedor |
| Evasión | uso de terminal/archivo fuera del MCP | solo toolset MCP | sin acceso directo al host | `/tools` y configuración real |

La **probabilidad** depende de qué herramientas vea el agente y de cuánto contenido no confiable procese. El **impacto** depende de los permisos del proceso. Por eso una defensa basada solo en «no leas secretos» escrita en el prompt es insuficiente: esa frase no reduce los privilegios del proceso [1][2].

## Arquitectura propuesta

`Usuario → Hermes (solo MCP del laboratorio) → supervisor con política fijada por operador → contenedor efímero → datos permitidos`

El supervisor y la política se ejecutan fuera de la conversación. El agente elige una acción solicitada, pero no el modo ni los permisos. En To-Be, el supervisor solo acepta lectura de `permitidos/`; la lectura se realiza en Docker con un único montaje de solo lectura. Los otros intentos se deniegan antes de ejecutar. La sonda de contenedor intenta saltarse la política para mostrar qué impide Docker por sí mismo. La auditoría se escribe en el host, fuera del montaje del contenedor.

## Qué puede demostrar y qué no

Una sesión real con Hermes que solo vea el MCP, junto con logs y sondas del contenedor, da evidencia de defensa por capas para este laboratorio. No prueba que Hermes sea seguro en toda configuración ni contra un atacante que pueda editar los perfiles locales, controlar Docker o explotar una vulnerabilidad del host. Tampoco prueba que una inyección de prompt siempre logre inducir la misma llamada: el comportamiento del modelo puede variar. Separaremos **intento del agente**, **decisión del supervisor** y **resultado del sistema operativo** en el análisis.

Fuentes: [1][2][3][4][5][6][7][8][10][11] en [REFERENCIAS.md](REFERENCIAS.md).
