# Resumen del Proyecto

## Calculadora

Este es un proyecto de ejemplo que implementa una **biblioteca mínima de operaciones aritméticas** en Python, acompañada de pruebas unitarias con **pytest**.

### Estructura del proyecto

- **`calc.py`**: Módulo principal que contiene las funciones aritméticas (por ejemplo, `sumar`).
- **`test_calc.py`**: Archivo de pruebas que valida el comportamiento de las funciones del módulo.
- **`conftest.py`**: Configuración adicional para pytest (fixtures o hooks compartidos).
- **`datos/`**: Directorio de datos del proyecto.

### Uso

```python
from calc import sumar
sumar(2, 3)  # Retorna 5
```

### Pruebas

Las pruebas se ejecutan con:

```bash
pytest
```
