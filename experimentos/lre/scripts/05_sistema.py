import json
import os
import random
import urllib.request
from collections import defaultdict

import pandas as pd

from comun import PERMITIDAS, URL_ACTUAL, consulta, guardar, proporcion, resumir, wilson

BASE = os.environ.get("TINKU_URL", "http://127.0.0.1:3000")
DEMO = {"correo": "demo@tinku.pe", "clave": "tinku2027"}
OBJETIVO = int(os.environ.get("EJERCICIOS", "3000"))
PERFILES = [
    ("quechua", "qullaw", {"variedad": "qullaw", "variedad_aimara": "sur"}),
    ("quechua", "chanka", {"variedad": "chanka", "variedad_aimara": "norte"}),
    ("aimara", "sur", {"variedad": "qullaw", "variedad_aimara": "sur"}),
    ("aimara", "norte", {"variedad": "chanka", "variedad_aimara": "norte"}),
]
OPUESTO = {"qullaw": "chanka", "chanka": "qullaw", "sur": "norte", "norte": "sur"}
ENFOQUES = ["", "", "puente", "significado", "escuchar"]
APRENDIBLE = ("length(glosa_es) <= 42 and forma not like '-%%' and categoria not like '%%propio%%' "
              "and categoria not like '%%Sufijo%%' and apta and principal")


def pedir(metodo, ruta, token=None, datos=None):
    req = urllib.request.Request(
        f"{BASE}/api{ruta}", method=metodo,
        data=json.dumps(datos).encode() if datos is not None else None,
        headers={"Content-Type": "application/json", **({"Authorization": f"Bearer {token}"} if token else {})})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read() or b"null")


def indices():
    lex = consulta(URL_ACTUAL, f"select id, lengua, lower(forma) forma, glosa_es, variedad, terminos from contenido.lexico where {APRENDIBLE}")
    por_forma, por_glosa = defaultdict(set), defaultdict(set)
    for r in lex.itertuples():
        por_forma[(r.lengua, r.forma)].add(r.variedad)
        por_glosa[(r.lengua, r.glosa_es)].add(r.variedad)
    todas = consulta(URL_ACTUAL, "select id, lengua, variedad, lower(forma) forma, glosa_es, terminos from contenido.lexico").set_index("id")
    return por_forma, por_glosa, todas


def main():
    random.seed(2027)
    por_forma, por_glosa, todas = indices()
    sesion = pedir("POST", "/auth/ingreso", datos=DEMO)
    token, original = sesion["token"], {k: sesion["usuario"][k] for k in ("variedad", "variedad_aimara")}
    filas = []
    try:
        for lengua, perfil, ajuste in PERFILES:
            pedir("PATCH", "/perfil", token, ajuste)
            otra = "aimara" if lengua == "quechua" else "quechua"
            permitidas = set(PERMITIDAS[(lengua, perfil)])
            opuestas = set(PERMITIDAS[(lengua, OPUESTO[perfil])])
            permitidas_otra = set(PERMITIDAS[(otra, ajuste["variedad_aimara"] if otra == "aimara" else ajuste["variedad"])])
            temas = [t["id"] for t in pedir("GET", f"/temas?lengua={lengua}", token)] + [""]
            n, llamadas = 0, 0
            while n < OBJETIVO and llamadas < OBJETIVO:
                llamadas += 1
                enfoque = random.choice(ENFOQUES)
                tema = random.choice(temas)
                cuerpo = {"lengua": lengua, "tema": tema or None, "cantidad": 30, **({"enfoque": enfoque} if enfoque else {})}
                for ej in pedir("POST", "/practica", token, cuerpo)["ejercicios"]:
                    if ej["tipo"] not in ("reconocer", "escuchar", "producir", "puente", "escribir"):
                        continue
                    n += 1
                    objetivo = todas.loc[ej["item_id"]]
                    fila = {"lengua": lengua, "perfil": perfil, "enfoque": enfoque or "(ninguno)", "tema": tema or "(todos)", "tipo": ej["tipo"],
                            "item_id": ej["item_id"], "variedad_objetivo": objetivo.variedad,
                            "objetivo_fuera": int(objetivo.variedad not in permitidas),
                            "objetivo_fuera_perfil_opuesto": int(objetivo.variedad not in opuestas),
                            "audio_hablante": int(bool(ej["audio"]) and ej["audio_origen"] == "hablante"),
                            "audio_no_hablante": int(bool(ej["audio"]) and ej["audio_origen"] != "hablante"),
                            "distractores": 0, "distractores_fuera": 0, "distractores_sin_entrada": 0, "distractores_fuera_perfil_opuesto": 0,
                            "puente_fuera": 0}
                    opciones = ej.get("opciones") or []
                    if ej["tipo"] in ("reconocer", "escuchar"):
                        correcta = objetivo.glosa_es
                        otras = [o for o in opciones if o != correcta]
                        conjuntos = [por_glosa.get((lengua, o)) for o in otras]
                        valido = permitidas
                    elif ej["tipo"] == "producir":
                        otras = [o for o in opciones if o.lower() != objetivo.forma]
                        conjuntos = [por_forma.get((lengua, o.lower())) for o in otras]
                        valido = permitidas
                    elif ej["tipo"] == "puente":
                        terminos = set(objetivo.terminos)
                        conjuntos_todos = [(o, por_forma.get((otra, o.lower()))) for o in opciones]
                        correctas = [o for o in opciones if any(set(t) & terminos for t in
                                     todas[(todas.lengua == otra) & (todas.forma == o.lower())].terminos)]
                        otras = [o for o in opciones if o not in correctas[:1]]
                        conjuntos = [c for o, c in conjuntos_todos if o in otras]
                        valido = permitidas_otra
                        for o in correctas[:1]:
                            fila["puente_fuera"] = int(not (por_forma.get((otra, o.lower()), set()) & valido))
                    else:
                        otras, conjuntos, valido = [], [], permitidas
                    fila["distractores"] = len(otras)
                    fila["distractores_sin_entrada"] = sum(c is None for c in conjuntos)
                    fila["distractores_fuera"] = sum(1 for c in conjuntos if c is not None and not (c & valido))
                    if ej["tipo"] != "puente":
                        fila["distractores_fuera_perfil_opuesto"] = sum(1 for c in conjuntos if c is not None and not (c & opuestas))
                    filas.append(fila)
    finally:
        pedir("PATCH", "/perfil", token, original)
    df = pd.DataFrame(filas)
    guardar(df, "sistema_ejercicios.csv")
    agregado = []
    for (lengua, perfil), g in df.groupby(["lengua", "perfil"], sort=False):
        for alcance, h in (("todos los enfoques", g), ("sin enfoque", g[g.enfoque == "(ninguno)"])):
            d = int(h.distractores.sum())
            k_obj, k_dis, k_aud = int(h.objetivo_fuera.sum()), int(h.distractores_fuera.sum()), int(h.audio_hablante.sum())
            agregado.append({"lengua": lengua, "perfil": perfil, "alcance": alcance, "ejercicios": len(h), "entradas_distintas": h.item_id.nunique(),
                             "objetivo_fuera": k_obj, "objetivo_fuera_prop": proporcion(k_obj, len(h)),
                             "objetivo_fuera_ic_sup": round(wilson(k_obj, len(h))[1], 6),
                             "control_objetivo_fuera_perfil_opuesto": int(h.objetivo_fuera_perfil_opuesto.sum()),
                             "control_distractores_fuera_perfil_opuesto": int(h.distractores_fuera_perfil_opuesto.fillna(0).sum()),
                             "puente": int((h.tipo == "puente").sum()), "puente_respuesta_fuera": int(h.puente_fuera.sum()),
                             "distractores": d, "distractores_fuera": k_dis, "distractores_fuera_prop": proporcion(k_dis, d),
                             "distractores_fuera_ic_sup": round(wilson(k_dis, d)[1], 6),
                             "distractores_sin_entrada": int(h.distractores_sin_entrada.sum()),
                             "con_audio_hablante": k_aud, "con_audio_hablante_prop": proporcion(k_aud, len(h)),
                             "con_audio_hablante_ic": [round(x, 6) for x in wilson(k_aud, len(h))],
                             "audio_no_hablante": int(h.audio_no_hablante.sum()),
                             "tipos": h.tipo.value_counts().to_dict()})
    a = pd.DataFrame(agregado)
    guardar(a.drop(columns=["tipos"]).assign(tipos=a.tipos.map(lambda d: json.dumps(d, ensure_ascii=False))), "sistema_resumen.csv")
    resumir("5_sistema", {"perfiles": agregado, "objetivo_por_perfil": OBJETIVO, "api": BASE,
                          "csv": ["resultados/sistema_ejercicios.csv", "resultados/sistema_resumen.csv"]})
    print(a.drop(columns=["tipos"]).to_string(index=False))


if __name__ == "__main__":
    main()
