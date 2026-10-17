# Entorno Docker de Aislamiento

## 1. Construcción de la Imagen

```bash
docker build -t secure-tools:latest -f docker/Dockerfile .
```

## 2. Parámetros de Ejecución

| Parámetro | Configuración | Propósito |
| :--- | :--- | :--- |
| `--network none` | Red deshabilitada | Bloqueo de conexiones externas y de red local. |
| `--read-only` | Filesystem de solo lectura | Bloqueo de escritura y modificación de archivos. |
| `-v ./datos/permitidos:/permitidos:ro` | Montaje de solo lectura | Acceso exclusivo a datos autorizados sin montar datos privados. |
| `--memory 128m --memory-swap 128m` | Límite de memoria | Restricción de consumo de RAM sin swap. |
| `--cpus 0.5` | Límite de CPU | Restricción de cuota de cómputo. |
| `timeout 2s` | Límite temporal | Detención forzada de tareas que superen 2 segundos. |
| `USER appuser` | Usuario sin privilegios | Ejecución en modo no root. |

## 3. Ejecución Directa

```bash
docker run --rm \
  --network none \
  --read-only \
  --memory 128m \
  --memory-swap 128m \
  --cpus 0.5 \
  -v "$(pwd)/datos/permitidos:/permitidos:ro" \
  secure-tools:latest \
  --tool T01 --ruta /permitidos/nota.txt
```
