import pandas as pd

from comun import (URL_ACTUAL, URL_ANTERIOR, consulta, fuentes, guardar, lexico_actual, lexico_anterior, oraciones_actual,
                   oraciones_anterior, proporcion, resumir)

MOTIVOS = {
    "panlex": "licencia no comercial (CC BY-NC-SA 4.0)",
    "minedu_americasnlp": "licencia no declarada por el distribuidor",
    "sintetico": "voz sintética: MMS-TTS (CC BY-NC 4.0), Gemini TTS (términos de servicio) y voz Paulina de macOS (licencia del sistema)",
}


def clase_licencia(licencia: str) -> str:
    t = (licencia or "").lower()
    if "by-nc" in t or "no comercial" in t:
        return "no comercial"
    if "no declarada" in t:
        return "no declarada"
    if "sintetic" in t:
        return "voz sintética"
    if t.startswith("cc0"):
        return "CC0"
    if "cc by-sa" in t and "cc0" in t:
        return "CC BY-SA / CC BY / CC0 (por archivo)"
    if "cc by-sa" in t:
        return "CC BY-SA"
    if "cc by" in t:
        return "CC BY"
    if "legal oficial" in t or "libre reproducción" in t:
        return "texto oficial / libre reproducción"
    return "otra"


def uso_comercial(clase: str) -> str:
    return "no" if clase in ("no comercial", "no declarada", "voz sintética", "otra") else "sí"


def conteos(lex: pd.DataFrame, ora: pd.DataFrame, fue: pd.DataFrame, momento: str) -> pd.DataFrame:
    filas = []
    for (f, lic), g in lex.groupby(["fuente_id", "licencia"]):
        filas.append({"fuente_id": f, "tipo": "léxico", "licencia": lic, momento: len(g),
                      f"{momento}_quechua": int((g.lengua == "quechua").sum()), f"{momento}_aimara": int((g.lengua == "aimara").sum()),
                      f"{momento}_aptas": int(g.apta.fillna(False).sum())})
    for (f, lic), g in ora.groupby(["fuente_id", "licencia"]):
        filas.append({"fuente_id": f, "tipo": "oraciones", "licencia": lic, momento: len(g),
                      f"{momento}_quechua": int((g.quechua != "").sum()), f"{momento}_aimara": int((g.aimara != "").sum())})
    audio = lex[lex.audio.fillna("") != ""]
    for origen, g in audio.groupby("audio_origen"):
        fuente = "lingua_libre" if origen == "hablante" else "sintetico"
        lic = fue.set_index("id").licencia.get("lingua_libre", "") if origen == "hablante" else "voz sintética"
        filas.append({"fuente_id": fuente, "tipo": "audio de palabras", "licencia": lic, momento: len(g),
                      f"{momento}_quechua": int((g.lengua == "quechua").sum()), f"{momento}_aimara": int((g.lengua == "aimara").sum())})
    usados = {(r["fuente_id"]) for r in filas}
    for _, r in fue.iterrows():
        if r.id not in usados and (r.registros or 0) > 0:
            filas.append({"fuente_id": r.id, "tipo": "evidencia o frases sin traducir", "licencia": r.licencia, momento: int(r.registros)})
    return pd.DataFrame(filas)


def main():
    lex0, lex1 = lexico_anterior(), lexico_actual()
    ora0, ora1 = oraciones_anterior(), oraciones_actual()
    fue0, fue1 = fuentes(URL_ANTERIOR), fuentes(URL_ACTUAL)
    a = conteos(lex0, ora0, fue0, "antes").rename(columns={"licencia": "licencia_antes"})
    d = conteos(lex1, ora1, fue1, "despues").rename(columns={"licencia": "licencia_despues"})
    sql = "select count(*) n from contenido.oraciones where coalesce(audio_es, '') <> '' or coalesce(audio_quechua, '') <> '' or coalesce(audio_aimara, '') <> ''"
    voz0, voz1 = int(consulta(URL_ANTERIOR, sql).n[0]), int(consulta(URL_ACTUAL, sql).n[0])
    a = pd.concat([a, pd.DataFrame([{"fuente_id": "sintetico", "tipo": "audio de oraciones", "licencia_antes": "voz sintética", "antes": voz0}])])
    d = pd.concat([d, pd.DataFrame([{"fuente_id": "sintetico", "tipo": "audio de oraciones", "licencia_despues": "voz sintética", "despues": voz1}])])
    t = a.merge(d, on=["fuente_id", "tipo"], how="outer")
    for c in t.columns:
        if c.startswith(("antes", "despues")):
            t[c] = t[c].fillna(0).astype(int)
    t["licencia"] = t.licencia_despues.fillna(t.licencia_antes)
    t["clase_licencia"] = t.licencia.map(clase_licencia)
    t.loc[t.fuente_id == "sintetico", "clase_licencia"] = "voz sintética"
    t["uso_comercial"] = t.clase_licencia.map(uso_comercial)
    t["estado"] = ["retirada" if r.despues == 0 and r.antes > 0 else "nueva" if r.antes == 0 and r.despues > 0 else "mantenida"
                   for r in t.itertuples()]
    t["motivo"] = [MOTIVOS.get(r.fuente_id, "") if r.estado == "retirada" else "" for r in t.itertuples()]
    t["cambio"] = t.despues - t.antes
    columnas = ["tipo", "fuente_id", "licencia", "clase_licencia", "uso_comercial", "estado", "motivo", "antes", "despues", "cambio",
                "antes_quechua", "despues_quechua", "antes_aimara", "despues_aimara", "antes_aptas", "despues_aptas"]
    t = t[columnas].sort_values(["tipo", "antes"], ascending=[True, False])
    guardar(t, "licencias_por_fuente.csv")

    resumen = {}
    for tipo, g in t.groupby("tipo"):
        antes, despues = int(g.antes.sum()), int(g.despues.sum())
        retirado = int(g[g.estado == "retirada"].antes.sum())
        resumen[tipo] = {"antes": antes, "despues": despues, "retirado_de_fuentes_retiradas": retirado,
                         "proporcion_retirada_del_total_anterior": proporcion(retirado, antes),
                         "por_fuente_retirada": {r.fuente_id: {"antes": int(r.antes), "proporcion_del_total_anterior": proporcion(int(r.antes), antes)}
                                                 for r in g[g.estado == "retirada"].itertuples()},
                         "despues_uso_comercial_no": int(g[g.uso_comercial == "no"].despues.sum())}
    lic0 = lex0.licencia.map(clase_licencia)
    resumen["léxico"]["antes_por_clase"] = lic0.value_counts().to_dict()
    resumen["léxico"]["despues_por_clase"] = lex1.licencia.map(clase_licencia).value_counts().to_dict()
    resumen["léxico"]["antes_quechua"] = int((lex0.lengua == "quechua").sum())
    resumen["léxico"]["antes_aimara"] = int((lex0.lengua == "aimara").sum())
    resumen["léxico"]["despues_quechua"] = int((lex1.lengua == "quechua").sum())
    resumen["léxico"]["despues_aimara"] = int((lex1.lengua == "aimara").sum())
    resumen["léxico"]["antes_aptas"] = int(lex0.apta.fillna(False).sum())
    resumen["léxico"]["despues_aptas"] = int(lex1.apta.fillna(False).sum())
    resumen["csv"] = "resultados/licencias_por_fuente.csv"
    resumir("1_licencias", resumen)
    print(t.to_string(index=False))


if __name__ == "__main__":
    main()
