import pandas as pd

from comun import (guardar, lexico_actual, lexico_anterior, oraciones_actual, oraciones_anterior, proporcion, rasgo_oracion,
                   resumir, variedades)

DECLARADA_ANTES = {"americasnli": "chanka", "flores200": "chanka", "minedu_americasnlp": "chanka", "dudh": "qullaw",
                   "constituciones": "mixta (que + quh)", "tatoeba": "sin declarar"}
SIN_DECLARAR = {"que", "qu"}


def marcar(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["rasgo"] = df.forma.fillna("").map(variedades.rasgo_qullaw)
    df["apta"] = df.apta.fillna(False).astype(bool)
    return df


def tabla_lexico(df: pd.DataFrame, momento: str) -> pd.DataFrame:
    filas = []
    for (lengua, variedad, fuente), g in df.groupby(["lengua", "variedad", "fuente_id"]):
        for subconjunto, h in (("todas", g), ("aptas", g[g.apta])):
            fila = {"corpus": momento, "lengua": lengua, "variedad": variedad or "(sin etiqueta)", "fuente_id": fuente, "subconjunto": subconjunto,
                    "entradas": len(h), "con_rasgo_collao": int((h.rasgo != "").sum())}
            for r in ("eyectiva", "aspirada", "progresivo_sha"):
                fila[r] = int((h.rasgo == r).sum())
            fila["iso_sin_variedad"] = int(h.iso.isin(SIN_DECLARAR).sum())
            filas.append(fila)
    return pd.DataFrame(filas)


def metricas(df: pd.DataFrame, momento: str) -> dict:
    q = df[df.lengua == "quechua"]
    a = df[df.lengua == "aimara"]
    salida = {}
    for subconjunto, qq, aa in (("todas", q, a), ("aptas", q[q.apta], a[a.apta])):
        ch = qq[qq.variedad == "chanka"]
        k = int((ch.rasgo != "").sum())
        sin_iso = int(qq.iso.isin(SIN_DECLARAR).sum())
        d = {"quechua": len(qq), "quechua_chanka": len(ch), "chanka_con_rasgo_collao": k,
             "chanka_con_rasgo_collao_proporcion": proporcion(k, len(ch)),
             "chanka_con_rasgo_por_tipo": ch[ch.rasgo != ""].rasgo.value_counts().to_dict(),
             "chanka_con_rasgo_por_fuente": ch[ch.rasgo != ""].fuente_id.value_counts().to_dict(),
             "quechua_iso_sin_variedad_declarada": sin_iso, "quechua_iso_sin_variedad_declarada_proporcion": proporcion(sin_iso, len(qq)),
             "aimara": len(aa), "aimara_norte_o_sur": int(aa.variedad.isin(["norte", "sur"]).sum()),
             "aimara_norte": int((aa.variedad == "norte").sum()), "aimara_sur": int((aa.variedad == "sur").sum())}
        if "variedad_evidencia" in qq:
            n = int((qq.variedad_evidencia == "neutra").sum())
            d["quechua_comun_neutra"] = n
            d["quechua_comun_neutra_proporcion"] = proporcion(n, len(qq))
        else:
            d["quechua_sin_variedad_etiquetada_en_sistema"] = int((qq.variedad.fillna("") == "").sum())
            qu = int((qq.iso == "qu").sum())
            d["quechua_iso_qu_etiquetado_qullaw"] = int(((qq.iso == "qu") & (qq.variedad == "qullaw")).sum())
            d["quechua_iso_qu"] = qu
        salida[subconjunto] = d
    return salida


def oraciones(df: pd.DataFrame, momento: str) -> pd.DataFrame:
    q = df[df.quechua != ""].copy()
    q["rasgo"] = q.quechua.map(rasgo_oracion)
    filas = []
    if "variedad_quechua" in q:
        grupos = q.groupby(["fuente_id", "variedad_quechua"])
    else:
        q["variedad_quechua"] = q.fuente_id.map(DECLARADA_ANTES).fillna("sin declarar")
        grupos = q.groupby(["fuente_id", "variedad_quechua"])
    for (fuente, variedad), g in grupos:
        filas.append({"corpus": momento, "fuente_id": fuente,
                      "variedad_quechua": variedad if momento == "despues" else "",
                      "variedad_declarada_por_la_fuente": DECLARADA_ANTES.get(fuente, "") if momento == "antes" else variedad,
                      "oraciones_con_quechua": len(g), "con_rasgo_collao": int((g.rasgo != "").sum()),
                      "eyectiva": int((g.rasgo == "eyectiva").sum()), "aspirada": int((g.rasgo == "aspirada").sum()),
                      "progresivo_sha": int((g.rasgo == "progresivo_sha").sum())})
    return pd.DataFrame(filas)


def main():
    lex0, lex1 = marcar(lexico_anterior()), marcar(lexico_actual())
    t = pd.concat([tabla_lexico(lex0, "antes"), tabla_lexico(lex1, "despues")])
    guardar(t, "fugas_variedad_lexico.csv")
    o0, o1 = oraciones(oraciones_anterior(), "antes"), oraciones(oraciones_actual(), "despues")
    o = pd.concat([o0, o1])
    guardar(o, "fugas_variedad_oraciones.csv")
    ch0 = o0[o0.variedad_declarada_por_la_fuente == "chanka"]
    ch1 = o1[o1.variedad_quechua == "chanka"]
    resumen = {
        "lexico_antes": metricas(lex0, "antes"),
        "lexico_despues": metricas(lex1, "despues"),
        "oraciones_antes": {
            "con_quechua": int(o0.oraciones_con_quechua.sum()),
            "con_quechua_sin_variedad_por_oracion": int(o0.oraciones_con_quechua.sum()),
            "fuentes_chanka_oraciones": int(ch0.oraciones_con_quechua.sum()),
            "fuentes_chanka_con_rasgo_collao": int(ch0.con_rasgo_collao.sum()),
            "fuentes_chanka_con_rasgo_collao_proporcion": proporcion(int(ch0.con_rasgo_collao.sum()), int(ch0.oraciones_con_quechua.sum())),
            "por_fuente_chanka": {r.fuente_id: [int(r.con_rasgo_collao), int(r.oraciones_con_quechua)] for r in ch0.itertuples()},
            "fuentes_sin_variedad_unica": int(o0[o0.variedad_declarada_por_la_fuente.isin(["sin declarar", "mixta (que + quh)"])].oraciones_con_quechua.sum()),
            "aimara_con_variedad": 0,
        },
        "oraciones_despues": {
            "con_quechua": int(o1.oraciones_con_quechua.sum()),
            "chanka": int(ch1.oraciones_con_quechua.sum()),
            "chanka_con_rasgo_collao": int(ch1.con_rasgo_collao.sum()),
            "qullaw": int(o1[o1.variedad_quechua == "qullaw"].oraciones_con_quechua.sum()),
            "sin_variedad": int(o1[o1.variedad_quechua == ""].oraciones_con_quechua.sum()),
        },
        "csv": ["resultados/fugas_variedad_lexico.csv", "resultados/fugas_variedad_oraciones.csv"],
        "nota": "antes: el sistema anterior derivaba la variedad del código ISO (quy → chanka; quz, quh, qu, qxp → qullaw; que → comun) y no tenía variedad en aimara ni en oraciones",
    }
    resumir("2_fugas_variedad", resumen)
    import json
    print(json.dumps(resumen, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
