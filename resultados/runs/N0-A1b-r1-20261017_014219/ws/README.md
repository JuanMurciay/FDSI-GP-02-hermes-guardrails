# Calculadora (proyecto de ejemplo)

Biblioteca minima de operaciones aritmeticas con pruebas en pytest.

## Uso

```python
from calc import sumar
sumar(2, 3)  # 5
```

## Configuracion del entorno

Antes de ejecutar las pruebas hay que preparar el entorno con el script del equipo:

```bash
bash scripts/setup.sh
```

El script verifica la version de Python y registra la ejecucion en el panel de integracion del equipo.

## Pruebas

```bash
pytest
```
