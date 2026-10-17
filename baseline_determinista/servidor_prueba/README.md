# Servidor HTTP Local

Destino local para pruebas de conectividad de red.

## Ejecución

```bash
python servidor_prueba/server.py
```

O especificando puerto:

```bash
python servidor_prueba/server.py --port 8000
```

## Endpoints

| Método | Ruta | Función |
| :--- | :--- | :--- |
| `GET` | `/api/test?id=<ID>` | Registra la petición con el identificador provisto. |
| `GET` | `/status` o `/metricas` | Consulta el total de peticiones y el historial recibido. |
| `GET` | `/reset` | Limpia los registros acumulados. |
