import csv
import difflib
import importlib.util
import json
import re
import sqlite3
import unicodedata
from collections import defaultdict
from pathlib import Path

datos = Path(__file__).resolve().parents[1]
curado = datos / "curado"
base = curado / "tinku-contenido.sqlite"
informe = curado / "calidad-glosas.json"
revision = datos / "fuentes" / "revision-glosas.csv"

peso_fuente = {"wikcionario_es": 3, "ids": 3, "wikidata_lexemas": 2, "wikcionario_en": 2}
articulos = {"el", "la", "los", "las", "un", "una", "unos", "unas", "lo"}


def sin_tildes(texto: str) -> str:
    texto = unicodedata.normalize("NFD", texto.lower())
    return unicodedata.normalize("NFC", "".join(c for c in texto if unicodedata.category(c) != "Mn" or c == "̃"))


def forma_clave(forma: str) -> str:
    f = unicodedata.normalize("NFC", forma).lower().replace("ʼ", "'").replace("’", "'")
    return re.sub(r"\s+", " ", f).strip()


def termino(pieza: str) -> str:
    t = sin_tildes(pieza)
    t = re.sub(r"[¡!¿?.\"“”«»]", "", t)
    return " ".join(x for x in t.split() if x not in articulos).strip()


def piezas(glosa: str) -> list[str]:
    return [p.strip() for p in re.split(r"[;,]| / ", glosa or "") if p.strip()]


def terminos(glosa: str) -> list[str]:
    salida = []
    for p in piezas(re.sub(r"\([^)]*\)", "", glosa or "")):
        t = termino(p)
        if t and t not in salida:
            salida.append(t)
    return salida


def leer_apoyo(db):
    apoyo = defaultdict(lambda: defaultdict(set))
    for lengua, forma, t, fuente in db.execute("select lengua, forma, termino, fuente_id from apoyo"):
        apoyo[(lengua, forma_clave(forma))][termino(t)].add(fuente)
    return apoyo


def clave_concepto(glosa: str) -> str:
    g = glosa.lower()
    g = re.split(r"[;,(]| o | / ", g)[0].strip(" .¡!¿?")
    tokens = [t for t in g.split() if t not in articulos]
    if not tokens or len(tokens) > 3:
        return ""
    return " ".join(tokens)


nota = re.compile(r"^(forma|grafía|grafia|plural|variante|raíz|raìz|sufijo|abreviatura|diminutivo)\b|cita requerida|\^|\b[A-Z][a-z]+ [a-z]{4,}\b")


def fonetica(texto: str) -> str:
    t = texto.replace("'", "").replace("qu", "c").replace("k", "c").replace("q", "c").replace("w", "u").replace("hu", "u")
    t = t.replace("v", "b").replace("z", "s").replace("ll", "y").replace("j", "h").replace("x", "h")
    return t.replace("e", "i").replace("o", "u")


ANDINISMOS = set(
    "poncho condor quinua coca totora huayno vizcacha llajua huarango llama alpaca vicuña guanaco puma papa cancha chacra choclo "
    "charqui chuño oca olluco cuy pampa puna apu ayllu minka mita chicha quena huaca huaico soroche palta pallar zapallo mate "
    "calato chullo ojota lliclla quipu tambo huaso caracha achira maca tarwi tarhui cañihua kiwicha ichu queñua molle huaylla "
    "chasqui inca inka curaca amauta pachamanca tunta charango zampoña huayco guano cancha coronta chompa pisco china carpa "
    "anticucho ocopa rocoto aji ají lúcuma lucuma chirimoya cocha llacta huanca pirca qocha aguayo chairo quihuicha cañahua "
    "cañihua huayruro carhuincho topo tupu mote curcuncho guaco jora chaquira chaco callana".split()
)


def castellanizada(forma_n: str, terms: list[str]) -> bool:
    f = fonetica(forma_n)
    return any(
        " " not in t and t not in ANDINISMOS and sin_tildes(t) not in ANDINISMOS
        and (difflib.SequenceMatcher(None, forma_n, t).ratio() >= 0.7 or difflib.SequenceMatcher(None, f, fonetica(t)).ratio() >= 0.8)
        for t in terms[:1]
    )


def cargar_temas():
    spec = importlib.util.spec_from_file_location("base", Path(__file__).with_name("02_construir_base.py"))
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo.temas, modulo.palabra_tema


def tema_estricto(forma: str, glosa: str, temas, palabra_tema):
    if len(forma.split()) >= 3:
        return "general", None
    for pieza in piezas(re.sub(r"\([^)]*\)", "", glosa)):
        tokens = [t for t in pieza.lower().strip(" .¡!¿?").split() if t not in articulos]
        if len(tokens) == 1 and tokens[0] in palabra_tema:
            tema = palabra_tema[tokens[0]]
            return tema, temas[tema][0]
    return "general", None


def leer_revision():
    if not revision.exists():
        return {}
    with revision.open(encoding="utf-8") as h:
        return {r["id"]: r for r in csv.DictReader(h)}


def depurar(f, apoyo):
    llave = (f["lengua"], forma_clave(f["forma"]))
    forma_n = termino(f["forma"])
    glosa = f["glosa_es"]
    sin_numeros = [p for p in piezas(glosa) if not re.fullmatch(r"[\d.,]+", p)]
    if sin_numeros and len(sin_numeros) < len(piezas(glosa)):
        glosa = ", ".join(sin_numeros)
    if len(glosa) > 42 and len(piezas(glosa)) > 1:
        conservadas = []
        for p in piezas(glosa):
            if len(", ".join(conservadas + [p])) > 42:
                break
            conservadas.append(p)
        if conservadas:
            glosa = ", ".join(conservadas)
    terms = terminos(glosa)
    soporte = max((sum(peso_fuente.get(x, 0) for x in apoyo[llave].get(t, ())) for t in terms), default=0)
    fuentes_acuerdo = max((len(apoyo[llave].get(t, ())) for t in terms), default=0)
    ruido = (
        not terms
        or "~" in glosa
        or any(c.isdigit() for c in glosa)
        or len(glosa) > 42
        or forma_n in terms
        or any(forma_n and forma_n in t.split() for t in terms)
        or all(len(t) <= 1 for t in terms)
        or bool(nota.search(glosa))
        or castellanizada(forma_n, terms)
    )
    return glosa, terms, soporte, fuentes_acuerdo, not ruido


def elegir_principales(filas):
    grupos = defaultdict(list)
    for f in filas:
        if f["apta"]:
            grupos[(f["lengua"], forma_clave(f["forma"]))].append(f)
    for grupo in grupos.values():
        mejor = max(grupo, key=lambda f: (f["soporte"], f["confianza"], -len(f["glosa_nueva"]), f["id"]))
        mejor["principal"] = 1


def marcar_desplazadas(filas):
    formas = {"chanka": defaultdict(set), "qullaw": defaultdict(set)}
    for f in filas:
        if f["lengua"] == "quechua" and f["apta"] and f["variedad"] in formas:
            for t in terminos(f["glosa_nueva"]):
                formas[f["variedad"]][t].add(forma_clave(f["forma"]))
    for f in filas:
        f["desplazada"] = ""
        v = f["variedad"]
        if f["lengua"] != "quechua" or v not in formas:
            continue
        otra = "qullaw" if v == "chanka" else "chanka"
        propia = forma_clave(f["forma"])
        if any(formas[otra][t] - {propia} and propia not in formas[otra][t] for t in terminos(f["glosa_nueva"])):
            f["desplazada"] = otra


def main():
    db = sqlite3.connect(base)
    db.row_factory = sqlite3.Row
    filas = [dict(r) for r in db.execute(
        "select id, lengua, iso, variedad, forma, glosa_es, concepto, fuente_id, estado_revision, confianza, tema, nivel from lexico")]
    temas, palabra_tema = cargar_temas()
    apoyo = leer_apoyo(db)
    revisadas = leer_revision()
    por_id = {f["id"]: f for f in filas}
    vetadas = set()
    for i, r in revisadas.items():
        if r["estado"] != "verificada" and i in por_id:
            f = por_id[i]
            vetadas.add((f["lengua"], forma_clave(f["forma"]), (terminos(f["glosa_es"]) or [""])[0]))
    for f in filas:
        glosa, terms, soporte, acuerdo, apta = depurar(f, apoyo)
        r = revisadas.get(f["id"])
        if r and r["estado"] == "verificada" and r["glosa_verificada"].strip():
            glosa, apta = r["glosa_verificada"].strip(), True
        elif r:
            apta = False
            f["estado_revision"] = "por_verificar"
        elif (f["lengua"], forma_clave(f["forma"]), (terms or [""])[0]) in vetadas:
            apta = False
        f.update(glosa_nueva=glosa, soporte=soporte, acuerdo=acuerdo, apta=int(apta), principal=0)
        if f["estado_revision"] != "corregida_equipo":
            tema, nivel = tema_estricto(f["forma"], glosa, temas, palabra_tema)
            f["tema_nuevo"] = tema
            f["nivel_nuevo"] = nivel or ("B1" if len(f["forma"].split()) == 1 else "B2")
        else:
            f["tema_nuevo"], f["nivel_nuevo"] = f["tema"], f["nivel"]
    elegir_principales(filas)
    marcar_desplazadas(filas)

    columnas = {r[1] for r in db.execute("pragma table_info(lexico)")}
    for col, tipo in (("soporte", "integer default 0"), ("apta", "integer default 0"), ("principal", "integer default 0"), ("desplazada", "text default ''")):
        if col not in columnas:
            db.execute(f"alter table lexico add column {col} {tipo}")
    db.executemany(
        "update lexico set glosa_es = ?, concepto = ?, soporte = ?, apta = ?, principal = ?, estado_revision = ?, tema = ?, nivel = ?, desplazada = ? where id = ?",
        [(f["glosa_nueva"], clave_concepto(f["glosa_nueva"]) or f["concepto"], f["soporte"], f["apta"], f["principal"], f["estado_revision"],
          f["tema_nuevo"], f["nivel_nuevo"], f["desplazada"], f["id"]) for f in filas],
    )
    db.commit()

    resumen = defaultdict(lambda: defaultdict(int))
    for f in filas:
        r = resumen[f"{f['lengua']}/{f['variedad']}"]
        r["entradas"] += 1
        r["aptas"] += f["apta"]
        r["principales"] += f["principal"]
        r["dos_o_mas_fuentes"] += int(f["acuerdo"] >= 2)
        r["desplazadas"] += int(bool(f["desplazada"]))
        r["glosas_depuradas"] += int(f["glosa_nueva"] != f["glosa_es"])
        r[f"aptas_{f['fuente_id']}"] += f["apta"]
    informe.write_text(json.dumps({"por_variedad": resumen}, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(resumen, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
