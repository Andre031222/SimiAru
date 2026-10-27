import csv

import pandas as pd

from comun import LISTAS, PERMITIDAS, guardar, lexico_actual, lexico_anterior, proporcion, resumir, variedades, wilson

LISTAS_BASICAS = {"Swadesh-1955-100": "Swadesh 100", "Tadmor-2009-100": "Leipzig–Jakarta", "Swadesh-1952-200": "Swadesh 200"}
FUENTES_ESPANOL = ["Swadesh-1961-100", "Key-2016-1310", "Huber-1992-375", "Rowe-1954-232", "Lastra-1986-381"]
ABIERTAS_ANTES = {"wikcionario_es", "wikidata_lexemas"}


def leer(nombre: str) -> list[dict]:
    with (LISTAS / f"{nombre}.tsv").open(encoding="utf-8") as h:
        return list(csv.DictReader(h, delimiter="\t"))


def espanol_por_concepto(fuentes_es: list[str]) -> dict[str, dict]:
    salida = {}
    for nombre in fuentes_es:
        for r in leer(nombre):
            if r.get("CONCEPTICON_ID") and r.get("SPANISH"):
                d = salida.setdefault(r["CONCEPTICON_ID"], {"glosas": [], "terminos": set(), "listas": []})
                d["glosas"].append(r["SPANISH"])
                d["terminos"] |= variedades.terminos(r["SPANISH"])
                d["listas"].append(nombre)
    return salida


def escenarios(lex0: pd.DataFrame, lex1: pd.DataFrame) -> dict:
    lex0 = lex0[lex0.apta.fillna(False).astype(bool)]
    lex1 = lex1[lex1.apta.fillna(False).astype(bool)]
    salida = {}
    for (lengua, perfil), permitidas in PERMITIDAS.items():
        if lengua == "quechua":
            antes = lex0[(lex0.lengua == lengua) & lex0.variedad.isin(permitidas)]
        else:
            antes = lex0[lex0.lengua == lengua]
        despues = lex1[(lex1.lengua == lengua) & lex1.variedad.isin(permitidas)]
        estricta = despues[~despues.variedad_evidencia.isin(["neutra", "sin_atestiguar"])]
        salida[(lengua, perfil)] = {
            "antes": antes,
            "antes_solo_fuentes_abiertas": antes[antes.fuente_id.isin(ABIERTAS_ANTES)],
            "despues": despues,
            "despues_sin_comun_no_atestiguado": estricta,
        }
    return salida


def indice(df: pd.DataFrame) -> dict[str, list[str]]:
    salida = {}
    for forma, glosa in zip(df.forma, df.glosa_es):
        for t in variedades.terminos(glosa or ""):
            salida.setdefault(t, []).append(forma)
    return salida


MAPAS = {"todas": FUENTES_ESPANOL, "sin_Key-2016-1310": [f for f in FUENTES_ESPANOL if f != "Key-2016-1310"]}


def main():
    lex0, lex1 = lexico_anterior(), lexico_actual()
    esc = escenarios(lex0, lex1)
    indices = {(k, n): indice(df) for k, d in esc.items() for n, df in d.items()}
    resumen = {}
    for mapa_es, fuentes_es in MAPAS.items():
        resumen[mapa_es] = calcular(mapa_es, espanol_por_concepto(fuentes_es), esc, indices)
    resumen["nota"] = "las glosas españolas de IDS (aimara) vienen de Key-2016-1310; el mapa sin_Key-2016-1310 controla esa circularidad"
    resumir("4_cobertura", resumen)


def calcular(mapa_es: str, espanol: dict, esc: dict, indices: dict) -> dict:
    sufijo = "" if mapa_es == "todas" else "_" + mapa_es.replace("-", "_").lower()

    mapa, detalle, filas = [], [], []
    for lista, etiqueta in LISTAS_BASICAS.items():
        conceptos = leer(lista)
        con_es = [c for c in conceptos if c["CONCEPTICON_ID"] in espanol]
        for c in conceptos:
            e = espanol.get(c["CONCEPTICON_ID"])
            mapa.append({"lista": lista, "numero": c["NUMBER"], "ingles": c["ENGLISH"], "concepticon_id": c["CONCEPTICON_ID"],
                         "concepticon_gloss": c["CONCEPTICON_GLOSS"], "glosas_es": " | ".join(e["glosas"]) if e else "",
                         "terminos_es": " | ".join(sorted(e["terminos"])) if e else "", "listas_es": " | ".join(e["listas"]) if e else "",
                         "incluido": bool(e)})
        for (lengua, perfil), d in esc.items():
            for nombre in d:
                ind = indices[((lengua, perfil), nombre)]
                k = 0
                for c in con_es:
                    formas = sorted({f for t in espanol[c["CONCEPTICON_ID"]]["terminos"] for f in ind.get(t, [])})
                    k += bool(formas)
                    detalle.append({"lista": lista, "lengua": lengua, "perfil": perfil, "escenario": nombre, "concepticon_id": c["CONCEPTICON_ID"],
                                    "ingles": c["ENGLISH"], "cubierto": int(bool(formas)), "formas": len(formas),
                                    "ejemplos": " | ".join(formas[:3])})
                n = len(con_es)
                lo, hi = wilson(k, n)
                filas.append({"mapa_es": mapa_es, "lista": lista, "nombre_lista": etiqueta, "lengua": lengua, "perfil": perfil, "escenario": nombre,
                              "conceptos_lista": len(conceptos), "conceptos_con_glosa_es": n, "cubiertos": k,
                              "proporcion": proporcion(k, n), "wilson_inf": round(lo, 6), "wilson_sup": round(hi, 6)})
    t = pd.DataFrame(filas)
    guardar(t, f"cobertura_basica{sufijo}.csv")
    guardar(pd.DataFrame(detalle), f"cobertura_basica_por_concepto{sufijo}.csv")
    guardar(pd.DataFrame(mapa), f"cobertura_mapa_conceptos_es{sufijo}.csv")
    resumen = {f"{r.lista}/{r.lengua}/{r.perfil}/{r.escenario}": {"cubiertos": int(r.cubiertos), "n": int(r.conceptos_con_glosa_es),
                                                                  "proporcion": r.proporcion, "ic95": [r.wilson_inf, r.wilson_sup]}
               for r in t.itertuples()}
    resumen["excluidos_sin_glosa_es"] = {l: [m["ingles"] for m in mapa if m["lista"] == l and not m["incluido"]] for l in LISTAS_BASICAS}
    resumen["csv"] = [f"resultados/cobertura_basica{sufijo}.csv", f"resultados/cobertura_basica_por_concepto{sufijo}.csv",
                      f"resultados/cobertura_mapa_conceptos_es{sufijo}.csv"]
    print(t[t.escenario.isin(["antes", "despues"])].to_string(index=False))
    return resumen


if __name__ == "__main__":
    main()
