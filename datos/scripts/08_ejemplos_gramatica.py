import csv
import json
import re
import sqlite3
from pathlib import Path

datos = Path(__file__).resolve().parents[1]
base = datos / "curado" / "tinku-contenido.sqlite"
unidades = json.loads((datos / "fuentes" / "gramatica.json").read_text(encoding="utf-8"))["unidades"]
salida = datos / "curado" / "gramatica_ejemplos.csv"

preferencia = {"americasnli": 0, "tatoeba": 1, "dudh": 2, "globalvoices_opus": 3, "flores200": 4}
excluidas = {"dudh", "globalvoices_opus", "constituciones"}
lexicalizadas = {
    "pa": {"papa"},
    "chu": {"wanachu"},
    "mpi": {"mayampi"},
    "ta": {"imaynata", "hawata", "achikyaqta", "chayta", "kayta"},
    "ru": {"akjamaru", "ukjamaru", "ukhamaru", "akhamaru"},
}
palabra = re.compile(r"[\w']+", re.UNICODE)
maximo = 300


def normal(texto):
    return texto.lower().replace("’", "'").replace("ʼ", "'")


def lemas(db, lengua):
    return {normal(f) for (f,) in db.execute("select forma from lexico where lengua = ? and (apta = 1 or soporte >= 2)", (lengua,))}


def verbal(unidad, sufijo, raiz, token, diccionario):
    if token in lexicalizadas.get(sufijo, set()) or "ch'" in raiz[-3:] and sufijo == "wan":
        return True
    if unidad["lengua"] == "quechua" and not unidad.get("raiz_verbal"):
        if sufijo in ("wan", "kuna") and raiz + "y" in diccionario:
            return True
        if sufijo == "man" and raiz.endswith(("y", "n", "nki")) and raiz[:-1] + "y" in diccionario:
            return True
        if sufijo == "yki" and raiz.endswith(("sqa", "spa", "ku", "na")):
            return True
        if sufijo == "kuna" and raiz.endswith(("y", "ku")):
            return True
    if unidad["id"] == "ay-posesivos" and raiz.endswith(("ña", "ta")):
        return True
    return False


def raices(unidad, raiz):
    candidatas = [raiz]
    if unidad["lengua"] == "quechua" and raiz.endswith("lla") and len(raiz) > 4:
        candidatas.append(raiz[:-3])
    if unidad.get("raiz_verbal"):
        candidatas = [c + "y" for c in candidatas]
    return candidatas


def legible(es, texto):
    return (
        es != es.upper()
        and not re.match(r"^\s*[0-9IVXL]+[.)º°-]", es)
        and len(es.split()) >= 3
        and not re.search(r"\b(mmm+|uf|eh+)\b|[0-9]", es.lower() + " " + texto.lower())
    )


def main():
    db = sqlite3.connect(base)
    diccionario = {l: lemas(db, l) for l in ("quechua", "aimara")}
    filas = []
    for u in unidades:
        col = u["lengua"]
        oraciones = [
            (i, re.sub(r"\s*'\s*", "'", t), e, f)
            for i, t, e, f in db.execute(f"select id, {col}, es, fuente_id from oraciones where {col} <> ''")
            if f not in excluidas or (f == "globalvoices_opus" and col == "aimara" and len(t.split()) <= 12)
        ]
        oraciones.sort(key=lambda o: (preferencia.get(o[3], 9), len(o[1])))
        encontrados = 0
        for oid, texto, es, fuente in oraciones:
            if encontrados >= maximo or not legible(es, texto):
                continue
            for posicion, m in enumerate(palabra.finditer(texto)):
                token = normal(m.group(0))
                for sufijo in u["sufijos"]:
                    raiz = token[: -len(sufijo)]
                    if not token.endswith(sufijo) or len(raiz) < 3 or token in diccionario[col]:
                        continue
                    if verbal(u, sufijo, raiz, token, diccionario[col]):
                        continue
                    if any(r in diccionario[col] for r in raices(u, raiz)):
                        filas.append({"unidad": u["id"], "oracion_id": oid, "posicion": posicion, "palabra": m.group(0),
                                      "raiz": m.group(0)[: -len(sufijo)], "sufijo": sufijo, "fuente_id": fuente,
                                      "antes": texto[: m.start()], "despues": texto[m.end():]})
                        encontrados += 1
                        break
                else:
                    continue
                break
        print(f"{u['id']:16s} {encontrados:4d} ejemplos")
    with salida.open("w", encoding="utf-8", newline="") as h:
        w = csv.DictWriter(h, fieldnames=["unidad", "oracion_id", "posicion", "palabra", "raiz", "sufijo", "fuente_id", "antes", "despues"])
        w.writeheader()
        w.writerows(filas)
    print(f"{len(filas)} ejemplos en {salida.name}")


if __name__ == "__main__":
    main()
