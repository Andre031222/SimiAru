import pandas as pd

from comun import guardar, lexico_actual, oraciones_actual, proporcion, resumir, variedades

RASGOS = {"eyectiva", "aspirada", "progresivo_sha"}


def regla(lengua: str, evidencia: str) -> str:
    if lengua == "aimara":
        if evidencia.startswith("crossandean_"):
            return "aimara: atestiguada en una sola localidad"
        if evidencia.startswith("ambas"):
            return "aimara: atestiguada en ambas localidades"
        return "aimara: sin atestiguar"
    if evidencia in RASGOS:
        return "1: rasgo exclusivo del Collao"
    if evidencia.startswith("ambas:"):
        return "2: atestiguada en ambas variedades"
    if evidencia == "neutra":
        return "4: sin evidencia (neutra)"
    return "3: atestiguada en una sola variedad"


def familia(token: str) -> str:
    if token in RASGOS:
        return "rasgo ortográfico/morfológico"
    if token.startswith("iso_") or token.startswith("wikcionario_"):
        return "etiqueta ISO o dialectal de la fuente"
    if token == "commonvoice_qxp":
        return "Common Voice qxp (Puno)"
    if token == "constituciones":
        return "corpus declarado Qullaw"
    if token in ("americasnli", "flores200"):
        return "corpus declarado Chanka"
    if token == "dudh":
        return "DUDH (quz, quh o quy)"
    if token.startswith("crossandean"):
        return "crossandean (lista por localidad)"
    if token in ("neutra", "sin_atestiguar"):
        return "sin evidencia"
    return "otra"


def tokens(evidencia: str) -> list[str]:
    e = evidencia.split(":", 1)[1] if evidencia.startswith("ambas:") else evidencia
    return [t for t in e.split("+") if t]


def main():
    lex = lexico_actual()
    lex["apta"] = lex.apta.fillna(False).astype(bool)
    lex["regla"] = [regla(l, e or "") for l, e in zip(lex.lengua, lex.variedad_evidencia)]
    lex["tipo_evidencia"] = [e if e in RASGOS or e in ("neutra", "sin_atestiguar") else
                             "ambas" if e.startswith("ambas") else "+".join(sorted({familia(t) for t in tokens(e)})) for e in lex.variedad_evidencia.fillna("")]
    t = (lex.groupby(["lengua", "variedad", "regla", "tipo_evidencia", "fuente_id"])
         .agg(entradas=("id", "size"), aptas=("apta", "sum")).reset_index())
    guardar(t, "clasificador_lexico.csv")

    filas = []
    for r in lex.itertuples():
        for tok in tokens(r.variedad_evidencia or ""):
            filas.append({"lengua": r.lengua, "variedad": r.variedad, "familia": familia(tok), "evidencia": tok, "id": r.id})
    ev = pd.DataFrame(filas)
    ev_f = ev.drop_duplicates(["id", "familia"]).groupby(["lengua", "variedad", "familia"]).size().reset_index(name="entradas_con_esta_evidencia")
    guardar(ev_f, "clasificador_evidencias_familia.csv")
    ev_t = ev.groupby(["lengua", "variedad", "evidencia"]).size().reset_index(name="entradas_con_esta_evidencia")
    guardar(ev_t, "clasificador_evidencias_detalle.csv")

    q = lex[lex.lengua == "quechua"].copy()
    q["rasgo"] = q.forma.fillna("").map(variedades.rasgo_qullaw)
    inconsistentes = int(((q.rasgo != "") & (q.variedad != "qullaw")).sum())
    rasgo_distinto = int(((q.rasgo != "") & (q.variedad_evidencia.isin(RASGOS)) & (q.rasgo != q.variedad_evidencia)).sum())

    ora = oraciones_actual()
    o = ora[ora.quechua != ""].groupby(["fuente_id", "variedad_quechua"]).size().reset_index(name="oraciones")
    guardar(o, "clasificador_oraciones.csv")

    por_regla = lex.groupby(["lengua", "regla"]).size()
    resumen = {
        "por_lengua_variedad": {f"{l}/{v}": int(n) for (l, v), n in lex.groupby(["lengua", "variedad"]).size().items()},
        "por_lengua_variedad_aptas": {f"{l}/{v}": int(n) for (l, v), n in lex.groupby(["lengua", "variedad"]).apta.sum().items()},
        "por_regla": {f"{l}/{r}": int(n) for (l, r), n in por_regla.items()},
        "por_regla_proporcion": {f"{l}/{r}": proporcion(int(n), int((lex.lengua == l).sum())) for (l, r), n in por_regla.items()},
        "quechua_qullaw_por_rasgo": q[q.variedad_evidencia.isin(RASGOS)].variedad_evidencia.value_counts().to_dict(),
        "entradas_con_evidencia_crossandean": int(lex.variedad_evidencia.fillna("").str.contains("crossandean").sum()),
        "entradas_con_evidencia_commonvoice": int(lex.variedad_evidencia.fillna("").str.contains("commonvoice_qxp").sum()),
        "entradas_en_puno": int(lex.en_puno.sum()),
        "control_rasgo_collao_no_qullaw": inconsistentes,
        "control_rasgo_recalculado_distinto": rasgo_distinto,
        "oraciones_por_variedad": {f"{f}/{v or '(sin quechua)'}": int(n) for f, v, n in o.itertuples(index=False)},
        "csv": ["resultados/clasificador_lexico.csv", "resultados/clasificador_evidencias_familia.csv",
                "resultados/clasificador_evidencias_detalle.csv", "resultados/clasificador_oraciones.csv"],
    }
    resumir("3_clasificador", resumen)
    import json
    print(json.dumps(resumen, ensure_ascii=False, indent=1))
    print(ev_f.to_string(index=False))


if __name__ == "__main__":
    main()
