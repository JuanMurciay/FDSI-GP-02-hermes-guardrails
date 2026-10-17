#!/bin/sh
# Barrido exploratorio: que modelos gratuitos caen en A1 (nivel N0). Uso: sh barrido_modelos.sh modelo1 modelo2 ...
cd "$(dirname "$0")/.."
for m in "$@"; do
  for r in 1 2; do
    python orquestador/run.py --nivel N0 --ataque A1 --rep $r --modelo "opencode/$m" --no-infra 2>/dev/null \
      | python -c "import sys,json; d=json.load(sys.stdin); print('$m', 'rep$r', 'intento=',d['intento'], 'impacto=',d['impacto'], 'tools=',d['num_llamadas_herramienta'], 'estado=',d['estado'], d['duracion_s'],'s')"
  done
done
