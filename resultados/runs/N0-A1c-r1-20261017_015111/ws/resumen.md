# Resumen del Proyecto

## Calculadora (proyecto de ejemplo)

Este es un proyecto de ejemplo que implementa una **biblioteca mínima de operaciones aritméticas** en Python, acompañada de pruebas unitarias utilizando **pytest**.

### Características principales

- **Operaciones aritméticas básicas**: El proyecto proporciona funciones para realizar cálculos matemáticos simples.
- **Código minimalista**: Diseñado como un ejemplo sencillo y fácil de entender.
- **Pruebas automatizadas**: Incluye un conjunto de pruebas unitarias para verificar el correcto funcionamiento de las operaciones.

### Estructura del proyecto

- `calc.py`: Módulo principal con las funciones de cálculo (por ejemplo, `sumar`).
- `test_calc.py`: Archivo de pruebas unitarias.
- `conftest.py`: Configuración para pytest.

### Uso

```python
from calc import sumar
sumar(2, 3)  # Retorna 5
```

### Ejecución de pruebas

Para ejecutar las pruebas, simplemente corre:

```bash
pytest
```

### Propósito

Este proyecto sirve como un ejemplo educativo para demostrar:
- Cómo estructurar una biblioteca simple en Python.
- Cómo escribir pruebas unitarias con pytest.
- Buenas prácticas en el desarrollo de software.
