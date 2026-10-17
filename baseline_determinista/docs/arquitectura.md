# Arquitectura de Aislamiento de Herramientas para Agentes

* **Equipo:** FDSI-GP-02
* **Asignatura:** Fundamentos de Seguridad (FDSI)
* **Integrantes:** Tomás Quiceno Ostos, Juan Sebastian Murcia Yanquen, Juan Manuel Villegas Medina, Daniel Julián Peña Bonilla

---

## 1. Problema de Seguridad

Un agente inteligente utiliza herramientas para interactuar con su entorno: leer y escribir archivos, enviar peticiones de red o ejecutar procesos en el sistema operativo anfitrión. Si estas herramientas cuentan con privilegios excesivos o carecen de fronteras de contención estrictas, una instrucción equivocada, una inyección de prompts indirecta o un comportamiento anómalo del modelo puede comprometer la confidencialidad, integridad y disponibilidad del sistema (**OWASP LLM06: Excessive Agency**).

El objetivo de esta investigación es medir empíricamente el impacto del aislamiento por contenedor sobre el comportamiento de herramientas simuladas ante peticiones potencialmente riesgosas según las directrices NIST AI 600-1 y NIST SP 800-190.

---

## 2. Pregunta de Investigación e Hipótesis

* **Pregunta:** ¿Qué cambia en el acceso a archivos, la comunicación por red y el consumo de tiempo y memoria cuando ejecutamos las mismas herramientas de un agente simulado con y sin restricciones de aislamiento?
* **Hipótesis:** La versión **Secure** impedirá leer archivos privados, modificar archivos de entrada y contactar el servidor de prueba. Asimismo, detendrá las tareas que superen el tiempo o la memoria permitidos, manteniendo inalterada la lectura de archivos autorizados. La versión **Unsecure** permitirá estas acciones dentro del entorno de prueba.

---

## 3. Diagramas de Arquitectura

### 3.1 Arquitectura Unsecure (Línea Base Sin Restricciones Específicas)

```mermaid
graph TD
    User["Usuario"] --> App["Aplicación Python: Agente Simulado"]
    App --> Exec["Ejecutor Unsecure"]
    
    subgraph Host["Entorno Local"]
        Exec --> Tools["Herramientas Simuladas<br/>(leer / escribir / HTTP / esperar / memoria)"]
        Tools -->|Lectura / Escritura directa| DatosAuth["/permitidos/nota.txt"]
        Tools -->|Lectura directa expuesta| DatosPriv["/privados/secreto.txt"]
        Tools -->|Tráfico HTTP sin filtro| Server["Servidor HTTP Local<br/>127.0.0.1:8000"]
    end
```

### 3.2 Arquitectura Secure (Contenedor Desechable con Principio de Menor Privilegio)

```mermaid
graph TD
    User["Usuario"] --> App["Aplicación Python: Agente Simulado"]
    App --> Exec["Ejecutor Secure<br/>(Monitoreo externo de tiempo y recursos)"]
    
    subgraph Container["Límite de Aislamiento: Contenedor Desechable"]
        direction TB
        Tools["Herramientas Simuladas (sin privilegios)"]
        MountRO["Volumen montado:<br/>Solo /permitidos en Solo Lectura (:ro)"]
        NoNet["Interfaz de red deshabilitada<br/>(--network none)"]
        ResourceLimit["Límites estrictos:<br/>2s timeout | 128 MiB RAM | 0.5 CPU"]
        
        Tools --> MountRO
        Tools -.->|Bloqueado| NoNet
        Tools -.->|Bloqueado por timeout/cgroup| ResourceLimit
    end

    Exec --> Container
    MountRO --> FileAuth["/permitidos/nota.txt (RO)"]
    
    OutsidePriv["/privados/secreto.txt<br/>(FUERA DEL CONTENEDOR)"]
    OutsideServer["Servidor HTTP Local<br/>(INALCANZABLE)"]

    Container -.-x|Sin acceso| OutsidePriv
    Container -.-x|Sin conexión| OutsideServer
```

---

## 4. Matriz de Pruebas Experimentales (T01 a T05)

| ID / Prueba | Condición / Entrada | Comportamiento Esperado Unsecure | Comportamiento Esperado Secure |
| :--- | :--- | :--- | :--- |
| **T01 · Lectura** | Leer `/permitidos/nota.txt` y luego `/privados/secreto.txt`. | Lee ambos archivos exitosamente. | Lee únicamente el autorizado; no obtiene el contenido privado. |
| **T02 · Escritura** | Intentar modificar el contenido de `/permitidos/nota.txt`. | Modifica y sobrescribe el archivo. | Escritura rechazada; archivo intacto (hash SHA-256 idéntico). |
| **T03 · Red** | HTTP GET al servidor local (`127.0.0.1:8000/api/test?id=...`). | El servidor recibe y registra la solicitud. | El servidor no recibe ninguna solicitud (`--network none`). |
| **T04 · Tiempo** | Herramienta que solicita espera de 10 segundos. | Finaliza tras esperar ~10 segundos. | El ejecutor detiene y elimina la herramienta al superar 2 segundos. |
| **T05 · Memoria** | Reservar y escribir 256 MiB de RAM durante 1 segundo. | Completa la reserva dentro del límite general. | No completa la reserva; se detiene por límite de memoria (128 MiB). |

---

## 5. Criterios de Evaluación y Umbrales Cuantitativos

| Métrica / Criterio | Método de Medición / Observación | Umbral Esperado en Secure (5 repeticiones) |
| :--- | :--- | :--- |
| **Acceso a archivos** | Conteo de lecturas autorizadas exitosas y privadas exitosas. | **5/5** autorizadas y **0/5** privadas. |
| **Integridad del archivo** | Comparación de hashes SHA-256 antes y después. | Archivo sin cambios en **5/5** casos. |
| **Bloqueo de red** | Conteo de peticiones con ID registradas en el servidor HTTP local. | **0 de 5** solicitudes recibidas. |
| **Límite de tiempo** | Medición de duración desde inicio hasta detención confirmada. | **5/5** detenidas en máximo 3 s (límite de 2 s + 1 s tolerancia). |
| **Límite de memoria** | Inspección de cuota de 128 MiB y conteo de reservas completadas. | **0/5** reservas completadas por restricción de memoria. |
