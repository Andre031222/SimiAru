#!/bin/sh
set -eu
cd "$(dirname "$0")"
dep="--with pandas --with psycopg[binary] --with openpyxl --with matplotlib"
uv run -q $dep python 01_licencias.py > /dev/null
uv run -q $dep python 02_fugas_variedad.py > /dev/null
uv run -q $dep python 03_clasificador.py > /dev/null
uv run -q $dep python 04_cobertura.py > /dev/null
uv run -q $dep python 05_sistema.py
uv run -q $dep python 06_kit_revision.py > /dev/null
uv run -q $dep python 07_figuras.py
