# FDSI-GP-02: Aislamiento de herramientas de un agente frente a inyección de instrucciones

Seminario "Seguridad de IA Generativa y Agentes Autónomos" (FDSI). Reformulación del
hito 1 (ver tag `hito-1` y `baseline_determinista/`): ahora un agente real con terminal
(opencode) es atacado con inyección de instrucciones indirecta, y se mide qué contiene
cada nivel de aislamiento cuando el modelo cae.

Ver la propuesta completa en `docs/Propuesta_FDSI_GP_02_v2.pdf` y los primeros
resultados en `resultados/RESULTADOS_30PCT.md`.

## Estructura

- `baseline_determinista/`: hito 1: agente simulado sin LLM, pruebas T01–T05 (línea base).
- `laboratorio/`: Dockerfile del agente, servidor del laboratorio/atacante, proxy con lista blanca + broker de credenciales (`proxy.py`) y política de validación de herramientas `N3` (`politicas/opencode.n3.json`).
- `tareas/proyecto_base/`: proyecto de ejemplo que el agente debe resumir/probar (tareas L1 y L2).
- `ataques/`: variantes de la inyección de instrucciones (A1, A1b, A1c).
- `orquestador/run.py`: corre un nivel (N0/N1/N2/N3) + ataque (+ `--broker` opcional) y mide intento/impacto.
- `resultados/`: registros por corrida (`runs/`) y `corridas.csv`.

## Ejecutar una corrida

```bash
python orquestador/run.py --nivel N0 --ataque A1c --rep 1
python orquestador/run.py --nivel N2 --ataque A1c --rep 1 --no-infra
python orquestador/run.py --nivel N2 --ataque none --tarea L2 --broker --rep 1
python orquestador/run.py --nivel N3 --ataque A1 --rep 1
```

## Pruebas locales del Broker de Credenciales y Nivel N3

```bash
python -m unittest laboratorio/test_broker_y_n3.py -v
```

Requiere Docker y una distro WSL `fdsi-lab` creada a partir de la imagen `fdsi-agent`
(ver `laboratorio/Dockerfile.agente`).
