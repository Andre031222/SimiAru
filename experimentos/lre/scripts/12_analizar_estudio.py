import argparse
import json
import math
from collections import Counter
from pathlib import Path

import pandas as pd

LRE = Path(__file__).resolve().parents[1]
Z = 1.959963984540054
PREDICCION = {"quechua": {"qullaw": "qullaw", "chanka": "chanka", "comun": "ambas"},
              "aimara": {"norte": "norte", "sur": "sur", "comun": "ambas"}}
NO_SE = "no_se"


def wilson(k: int, n: int) -> list[float]:
    if n == 0:
        return [float("nan"), float("nan")]
    p = k / n
    d = 1 + Z * Z / n
    c = (p + Z * Z / (2 * n)) / d
    m = Z * math.sqrt(p * (1 - p) / n + Z * Z / (4 * n * n)) / d
    return [round(max(0.0, c - m), 6), round(min(1.0, c + m), 6)]


def proporcion(k: int, n: int) -> dict:
    return {"n": n, "aciertos": k, "proporcion": round(k / n, 6) if n else float("nan"), "ic95_wilson": wilson(k, n)}


def alfa_nominal(unidades: list[list[str]]) -> dict:
    coincidencias = Counter()
    for valores in unidades:
        valores = [v for v in valores if v]
        m = len(valores)
        if m < 2:
            continue
        cuenta = Counter(valores)
        for c in cuenta:
            for k in cuenta:
                pares = cuenta[c] * (cuenta[k] - (1 if c == k else 0))
                if pares:
                    coincidencias[(c, k)] += pares / (m - 1)
    marginal = Counter()
    for (c, _), v in coincidencias.items():
        marginal[c] += v
    n = sum(marginal.values())
    pareables = sum(1 for u in unidades if len([v for v in u if v]) >= 2)
    if n <= 1:
        return {"alfa": float("nan"), "unidades": pareables, "valores": round(n, 6)}
    observado = sum(v for (c, k), v in coincidencias.items() if c != k)
    esperado = sum(marginal[c] * marginal[k] for c in marginal for k in marginal if c != k)
    alfa = 1.0 if esperado == 0 and observado == 0 else (1 - (n - 1) * observado / esperado if esperado else float("nan"))
    return {"alfa": round(alfa, 6), "unidades": pareables, "valores": round(n, 6)}


def mayoria(valores: list[str]) -> str:
    valores = [v for v in valores if v]
    if not valores:
        return ""
    valor, veces = Counter(valores).most_common(1)[0]
    return valor if veces * 2 > len(valores) else ""


def leer(respuestas: Path, participantes: Path, solo_nativos: bool) -> pd.DataFrame:
    r = pd.read_csv(respuestas, dtype=str, encoding="utf-8-sig").fillna("")
    p = pd.read_csv(participantes, dtype=str, encoding="utf-8-sig").fillna("")
    if solo_nativos:
        p = p[p.nativo == "si"]
    r = r[r.evaluador.isin(set(p.evaluador))]
    r["codigo"] = r.codigo.str.lstrip("'")
    return r


def analizar(lengua: str, clave: pd.DataFrame, r: pd.DataFrame) -> tuple[dict, pd.DataFrame]:
    clave = clave[clave.lengua == lengua].copy()
    r = r[r.lengua == lengua]
    filas = []
    for _, k in clave.iterrows():
        g = r[r.codigo == k.codigo]
        glosas = list(g.glosa)
        variedades = list(g.variedad)
        filas.append({
            "codigo": k.codigo,
            "clase": k.clase,
            "variedad_predicha": k.variedad_predicha,
            "prediccion": PREDICCION[lengua].get(k.variedad_predicha, ""),
            "evaluadores": int(((g.glosa != "") | (g.variedad != "")).sum()),
            "glosas": ";".join(v for v in glosas if v),
            "variedades": ";".join(v for v in variedades if v),
            "glosa_consenso": mayoria(glosas),
            "variedad_consenso": mayoria([v for v in variedades if v != NO_SE]),
        })
    df = pd.DataFrame(filas)
    df["variedad_exacta"] = [int(p == c) if c else None for p, c in zip(df.prediccion, df.variedad_consenso)]
    df["variedad_compatible"] = [int(c == p or (p != "ambas" and c == "ambas")) if c else None for p, c in zip(df.prediccion, df.variedad_consenso)]
    unidades = {c: g for c, g in r.groupby("codigo")}
    def alfas(codigos, sin_no_se=False):
        u_g = [list(unidades[c].glosa) for c in codigos if c in unidades]
        u_v = [[v for v in unidades[c].variedad if not (sin_no_se and v == NO_SE)] for c in codigos if c in unidades]
        return {"glosa": alfa_nominal(u_g), "variedad": alfa_nominal(u_v)} | ({} if sin_no_se else {"variedad_sin_no_se": alfa_nominal(
            [[v for v in unidades[c].variedad if v != NO_SE] for c in codigos if c in unidades])["alfa"]})
    def exito(g, columna):
        v = g[columna].dropna().astype(int)
        return proporcion(int(v.sum()), len(v))
    def glosa(g, aceptadas):
        v = g[g.glosa_consenso != ""]
        return proporcion(int(v.glosa_consenso.isin(aceptadas).sum()), len(v))
    resultado = {
        "items": len(df),
        "evaluadores": int(r.evaluador.nunique()),
        "items_con_respuesta": int((df.evaluadores > 0).sum()),
        "evaluadores_por_item": {str(k): int(v) for k, v in sorted(Counter(df.evaluadores).items())},
        "media_evaluadores_por_item": round(float(df.evaluadores.mean()), 6) if len(df) else float("nan"),
        "consenso_glosa": int((df.glosa_consenso != "").sum()),
        "consenso_variedad": int((df.variedad_consenso != "").sum()),
        "por_clase": {},
    }
    for nombre, g in [("todas", df)] + list(df.groupby("clase")):
        resultado["por_clase"][nombre] = {
            "items": len(g),
            "alfa_krippendorff": alfas(list(g.codigo)),
            "glosa_correcta": glosa(g, {"si"}),
            "glosa_correcta_o_parcial": glosa(g, {"si", "parcial"}),
            "variedad_exacta": exito(g, "variedad_exacta"),
            "variedad_compatible": exito(g, "variedad_compatible"),
        }
    return resultado, df


def tabla(lengua: str, resultado: dict) -> list[dict]:
    filas = []
    for clase, d in resultado["por_clase"].items():
        fila = {"lengua": lengua, "clase": clase, "items": d["items"],
                "alfa_glosa": d["alfa_krippendorff"]["glosa"]["alfa"], "alfa_variedad": d["alfa_krippendorff"]["variedad"]["alfa"],
                "alfa_variedad_sin_no_se": d["alfa_krippendorff"]["variedad_sin_no_se"]}
        for medida in ("glosa_correcta", "glosa_correcta_o_parcial", "variedad_exacta", "variedad_compatible"):
            m = d[medida]
            fila |= {f"{medida}_n": m["n"], f"{medida}_k": m["aciertos"], f"{medida}_p": m["proporcion"],
                     f"{medida}_ic_inf": m["ic95_wilson"][0], f"{medida}_ic_sup": m["ic95_wilson"][1]}
        filas.append(fila)
    return filas


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--respuestas", required=True, type=Path)
    p.add_argument("--participantes", required=True, type=Path)
    p.add_argument("--clave", type=Path, default=LRE / "revision" / "clave-oculta.csv")
    p.add_argument("--salida", type=Path, default=LRE / "resultados" / "estudio")
    p.add_argument("--solo-nativos", action="store_true")
    a = p.parse_args()
    clave = pd.read_csv(a.clave, dtype=str)
    r = leer(a.respuestas, a.participantes, a.solo_nativos)
    a.salida.mkdir(parents=True, exist_ok=True)
    sufijo = "-nativos" if a.solo_nativos else ""
    filas = []
    for lengua in ("quechua", "aimara"):
        resultado, df = analizar(lengua, clave, r)
        resultado["solo_nativos"] = a.solo_nativos
        (a.salida / f"estudio-{lengua}{sufijo}.json").write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")
        df.to_csv(a.salida / f"estudio-{lengua}{sufijo}-items.csv", index=False)
        filas += tabla(lengua, resultado)
        print(f"{lengua}: {resultado['evaluadores']} evaluadores, {resultado['items_con_respuesta']} ítems con respuesta, "
              f"alfa glosa {resultado['por_clase']['todas']['alfa_krippendorff']['glosa']['alfa']}, "
              f"alfa variedad {resultado['por_clase']['todas']['alfa_krippendorff']['variedad']['alfa']}")
    pd.DataFrame(filas).to_csv(a.salida / f"estudio-tabla{sufijo}.csv", index=False)


if __name__ == "__main__":
    main()
