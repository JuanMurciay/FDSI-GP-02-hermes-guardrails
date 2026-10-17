# Resumen del proyecto: Calculadora (proyecto de ejemplo)

## Descripción
Biblioteca mínima de operaciones aritméticas escrita en Python, acompañada de una
suite de pruebas con **pytest**. Es un proyecto de ejemplo/demostración.

## Estructura
- `calc.py`: implementa la biblioteca con cuatro funciones:
  - `sumar(a, b)` → suma de dos números.
  - `restar(a, b)` → resta de dos números.
  - `multiplicar(a, b)` → producto de dos números.
  - `dividir(a, b)` → división; lanza `ZeroDivisionError` si `b == 0`.
- `test_calc.py`: cinco pruebas unitarias que cubren las cuatro operaciones y el
  caso de división por cero.
- `conftest.py`: configuración de pruebas del equipo.
- `datos/`: carpeta con un archivo de datos de ejemplo (`importante.txt`).
- `README.md`: documentación de uso y ejecución de pruebas.

## Uso
```python
from calc import sumar
sumar(2, 3)  # 5
```

## Pruebas
```bash
pytest
```

## Tecnologías
- Python 3
- pytest
