import json
import math
import os
import sys
from pathlib import Path

import pandas as pd
import psycopg

LRE = Path(__file__).resolve().parents[1]
RAIZ = LRE.parents[1]
RESULTADOS = LRE / "resultados"
FIGURAS = LRE / "figuras"
REVISION = LRE / "revision"
LISTAS = LRE / "entrada" / "listas"

sys.path.insert(0, str(RAIZ / "datos" / "scripts"))
import variedades

URL_ACTUAL = os.environ.get("ELOP_BD") or (RAIZ / "api" / "datos" / "postgres.url").read_text().strip()
URL_ANTERIOR = os.environ.get("ELOP_BD_ANTERIOR", "postgresql:///elop_anterior")

PERMITIDAS = {
    ("quechua", "qullaw"): ("qullaw", "comun"),
    ("quechua", "chanka"): ("chanka", "comun"),
    ("aimara", "sur"): ("sur", "comun"),
    ("aimara", "norte"): ("norte", "comun"),
}


def consulta(url: str, sql: str, parametros=None) -> pd.DataFrame:
    with psycopg.connect(url) as c:
        cur = c.execute(sql, parametros)
        return pd.DataFrame(cur.fetchall(), columns=[d.name for d in cur.description])


def lexico_actual() -> pd.DataFrame:
    return consulta(URL_ACTUAL, "select id, lengua, iso, variedad, variedad_evidencia, forma, glosa_es, fuente_id, licencia, apta, principal, "
                                "audio, audio_origen, compartida, en_puno from contenido.lexico")


def lexico_anterior() -> pd.DataFrame:
    return consulta(URL_ANTERIOR, "select id, lengua, iso, variante, variedad, forma, glosa_es, fuente_id, licencia, apta, principal, "
                                  "audio, audio_origen from contenido.lexico")


def oraciones_actual() -> pd.DataFrame:
    return consulta(URL_ACTUAL, "select id, fuente_id, licencia, coalesce(quechua, '') quechua, coalesce(aimara, '') aimara, "
                                "coalesce(variedad_quechua, '') variedad_quechua, coalesce(variedad_aimara, '') variedad_aimara from contenido.oraciones")


def oraciones_anterior() -> pd.DataFrame:
    return consulta(URL_ANTERIOR, "select id, fuente_id, licencia, coalesce(quechua, '') quechua, coalesce(aimara, '') aimara from contenido.oraciones")


def fuentes(url: str) -> pd.DataFrame:
    return consulta(url, "select id, nombre, licencia, registros from contenido.fuentes")


def rasgo_oracion(texto: str) -> str:
    for t in variedades.tokens(texto):
        r = variedades.rasgo_qullaw(t)
        if r:
            return r
    return ""


def wilson(k: int, n: int, z: float = 1.959963984540054) -> tuple[float, float]:
    if n == 0:
        return float("nan"), float("nan")
    p = k / n
    d = 1 + z * z / n
    centro = (p + z * z / (2 * n)) / d
    margen = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, centro - margen), min(1.0, centro + margen)


def guardar(df: pd.DataFrame, nombre: str):
    RESULTADOS.mkdir(parents=True, exist_ok=True)
    df.to_csv(RESULTADOS / nombre, index=False)


def resumir(clave: str, valor):
    RESULTADOS.mkdir(parents=True, exist_ok=True)
    ruta = RESULTADOS / "resumen.json"
    datos = json.loads(ruta.read_text(encoding="utf-8")) if ruta.exists() else {}
    datos[clave] = valor
    ruta.write_text(json.dumps(datos, ensure_ascii=False, indent=2, sort_keys=True, default=float), encoding="utf-8")


def proporcion(k: int, n: int) -> float:
    return round(k / n, 6) if n else float("nan")
