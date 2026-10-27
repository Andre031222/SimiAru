import argparse
import json
import math
from collections import Counter
from pathlib import Path

import pandas as pd

Z = 1.959963984540054
PREDICCION = {"quechua": {"qullaw": "Collao", "chanka": "Chanka", "comun": "ambas"},
              "aimara": {"norte": "norteño", "sur": "sureño", "comun": "ambos"}}
AMBAS = {"quechua": "ambas", "aimara": "ambos"}
NO_SE = "no sé"
CANONICO = {"si": "sí", "no se": NO_SE, "collao": "Collao", "qullaw": "Collao", "chanka": "Chanka", "ambos": "ambos", "ambas": "ambas",
            "norteno": "norteño", "sureno": "sureño"}


def wilson(k: int, n: int) -> list[float]:
    if n == 0:
        return [float("nan"), float("nan")]
    p = k / n
    d = 1 + Z * Z / n
    c = (p + Z * Z / (2 * n)) / d
    m = Z * math.sqrt(p * (1 - p) / n + Z * Z / (4 * n * n)) / d
    return [round(max(0.0, c - m), 6), round(min(1.0, c + m), 6)]


def kappa(a: list[str], b: list[str]) -> dict:
    pares = [(x, y) for x, y in zip(a, b) if x and y]
    n = len(pares)
    if n == 0:
        return {"n": 0, "kappa": float("nan"), "acuerdo_observado": float("nan")}
    po = sum(x == y for x, y in pares) / n
    ca, cb = Counter(x for x, _ in pares), Counter(y for _, y in pares)
    pe = sum(ca[k] * cb[k] for k in set(ca) | set(cb)) / (n * n)
    k = (po - pe) / (1 - pe) if pe < 1 else float("nan")
    return {"n": n, "kappa": round(k, 6), "acuerdo_observado": round(po, 6), "acuerdo_esperado": round(pe, 6)}


def normal(v) -> str:
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return ""
    t = str(v).strip().lower()
    return CANONICO.get(t, t)


def leer(ruta: Path) -> pd.DataFrame:
    df = pd.read_excel(ruta, sheet_name="revision", dtype=str)
    df = df.iloc[:, :6]
    df.columns = ["codigo", "forma", "glosa_es", "glosa", "variedad", "comentario"]
    df["glosa"] = df.glosa.map(normal)
    df["variedad"] = df.variedad.map(normal)
    return df[["codigo", "glosa", "variedad"]]


def proporciones(g: pd.DataFrame, columna: str, exito) -> dict:
    validos = g[g[columna] != ""]
    k = int(validos[columna].map(exito).sum())
    return {"n": len(validos), "aciertos": k, "proporcion": round(k / len(validos), 6) if len(validos) else float("nan"),
            "ic95_wilson": wilson(k, len(validos))}


def analizar(lengua: str, clave: pd.DataFrame, r1: pd.DataFrame, r2: pd.DataFrame) -> tuple[dict, pd.DataFrame]:
    clave = clave[clave.lengua == lengua]
    df = clave.merge(r1, on="codigo", how="left").merge(r2, on="codigo", how="left", suffixes=("_r1", "_r2"))
    for c in ("glosa_r1", "glosa_r2", "variedad_r1", "variedad_r2"):
        df[c] = df[c].fillna("")
    df["prediccion"] = df.variedad_predicha.map(PREDICCION[lengua])
    df["glosa_consenso"] = [x if x and x == y else "" for x, y in zip(df.glosa_r1, df.glosa_r2)]
    df["variedad_consenso"] = [x if x and x == y and x != NO_SE else "" for x, y in zip(df.variedad_r1, df.variedad_r2)]
    ambas = AMBAS[lengua]
    df["variedad_exacta"] = [int(p == c) if c else None for p, c in zip(df.prediccion, df.variedad_consenso)]
    df["variedad_compatible"] = [int(c == p or (p != ambas and c == ambas)) if c else None for p, c in zip(df.prediccion, df.variedad_consenso)]
    sin_nose = lambda s: [x if x != NO_SE else "" for x in s]
    resultado = {
        "items": len(df),
        "respondidos_r1": int(((df.glosa_r1 != "") | (df.variedad_r1 != "")).sum()),
        "respondidos_r2": int(((df.glosa_r2 != "") | (df.variedad_r2 != "")).sum()),
        "kappa_glosa": kappa(list(df.glosa_r1), list(df.glosa_r2)),
        "kappa_variedad": kappa(list(df.variedad_r1), list(df.variedad_r2)),
        "kappa_variedad_sin_no_se": kappa(sin_nose(df.variedad_r1), sin_nose(df.variedad_r2)),
        "consenso_glosa": int((df.glosa_consenso != "").sum()),
        "consenso_variedad": int((df.variedad_consenso != "").sum()),
    }
    por_clase = {}
    for nombre, g in [("todas", df)] + list(df.groupby("clase")):
        por_clase[nombre] = {
            "glosa_correcta": proporciones(g, "glosa_consenso", lambda v: v == "sí"),
            "glosa_correcta_o_parcial": proporciones(g, "glosa_consenso", lambda v: v in ("sí", "parcial")),
            "glosa_correcta_r1": proporciones(g, "glosa_r1", lambda v: v == "sí"),
            "glosa_correcta_r2": proporciones(g, "glosa_r2", lambda v: v == "sí"),
            "variedad_exacta": _exito(g, "variedad_exacta"),
            "variedad_compatible": _exito(g, "variedad_compatible"),
            "kappa_variedad": kappa(list(g.variedad_r1), list(g.variedad_r2)),
        }
    resultado["por_clase"] = por_clase
    return resultado, df


def _exito(g: pd.DataFrame, columna: str) -> dict:
    v = g[columna].dropna().astype(int)
    k, n = int(v.sum()), len(v)
    return {"n": n, "aciertos": k, "proporcion": round(k / n, 6) if n else float("nan"), "ic95_wilson": wilson(k, n)}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--lengua", required=True, choices=["quechua", "aimara"])
    p.add_argument("--clave", required=True, type=Path)
    p.add_argument("--r1", required=True, type=Path)
    p.add_argument("--r2", required=True, type=Path)
    p.add_argument("--salida", required=True, type=Path)
    a = p.parse_args()
    clave = pd.read_csv(a.clave, dtype=str)
    resultado, df = analizar(a.lengua, clave, leer(a.r1), leer(a.r2))
    a.salida.mkdir(parents=True, exist_ok=True)
    (a.salida / f"revision-{a.lengua}.json").write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")
    df.drop(columns=["forma", "glosa_es"]).to_csv(a.salida / f"revision-{a.lengua}-items.csv", index=False)
    filas = []
    for clase, d in resultado["por_clase"].items():
        for medida in ("glosa_correcta", "glosa_correcta_o_parcial", "variedad_exacta", "variedad_compatible"):
            m = d[medida]
            filas.append({"lengua": a.lengua, "clase": clase, "medida": medida, "n": m["n"], "aciertos": m["aciertos"],
                          "proporcion": m["proporcion"], "ic95_inf": m["ic95_wilson"][0], "ic95_sup": m["ic95_wilson"][1]})
        filas.append({"lengua": a.lengua, "clase": clase, "medida": "kappa_variedad", "n": d["kappa_variedad"]["n"],
                      "proporcion": d["kappa_variedad"]["kappa"]})
    pd.DataFrame(filas).to_csv(a.salida / f"revision-{a.lengua}-tabla.csv", index=False)
    print(json.dumps({k: v for k, v in resultado.items() if k != "por_clase"}, ensure_ascii=False, indent=1))
    print(pd.DataFrame(filas).to_string(index=False))


if __name__ == "__main__":
    main()
