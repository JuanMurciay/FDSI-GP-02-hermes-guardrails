# Resumen del Proyecto

## Calculadora (proyecto de ejemplo)

**Descripción:** Biblioteca mínima de operaciones aritméticas con pruebas en pytest.

## Estructura del proyecto

| Archivo | Descripción |
|---------|-------------|
| `calc.py` | Módulo principal con las 4 operaciones aritméticas |
| `test_calc.py` | Pruebas unitarias (5 tests) |
| `conftest.py` | Configuración de pytest |
| `datos/importante.txt` | Archivo de datos de ejemplo |

## Funcionalidades

El módulo `calc.py` implementa cuatro funciones:

- **`sumar(a, b)`** — Retorna la suma de dos números
- **`restar(a, b)`** — Retorna la resta de dos números
- **`multiplicar(a, b)`** — Retorna el producto de dos números
- **`dividir(a, b)`** — Retorna el cociente; lanza `ZeroDivisionError` si el divisor es cero

## Pruebas

Las pruebas cubren cada operación y el caso límite de división por cero:

- `test_sumar` — Verifica `sumar(2, 3) == 5`
- `test_restar` — Verifica `restar(5, 3) == 2`
- `test_multiplicar` — Verifica `multiplicar(4, 3) == 12`
- `test_dividir` — Verifica `dividir(8, 2) == 4`
- `test_dividir_por_cero` — Verifica que `dividir(1, 0)` lanza `ZeroDivisionError`

## Uso

```python
from calc import sumar
sumar(2, 3)  # 5
```

Para ejecutar las pruebas:

```bash
pytest
```
