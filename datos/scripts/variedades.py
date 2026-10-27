import csv
import re
import unicodedata
from collections import defaultdict
from pathlib import Path

datos = Path(__file__).resolve().parents[1]
crudo = datos / "fuentes" / "crudo"
curado = datos / "curado"

ISO_QULLAW = {"quz", "qxp", "quh"}
ISO_CHANKA = {"quy"}

ANDINO_QULLAW = {"Puno", "Cuzco", "Taquile", "Arma", "Maragua", "Pocona", "Curva"}
ANDINO_CHANKA = {"Ayacucho", "Atalla"}
ANDINO_NORTE = "Huancane"
ANDINO_SUR = "Sullkatiti"

EYECTIVA = re.compile(r"(ch|p|t|k|q)'")
ASPIRADA = re.compile(r"(chh|ph|th|kh|qh)(?!ina)")
PROGRESIVO_SHA = re.compile(r"^\w{2,}(sha|sya)(n|ni|nki|nchik|nchis|nku|nkichik|yku|ykuku|spa|rqa\w*|chun|nqa|ptin)$")
AJENA = re.compile(r"[bcdfgvxz]|the|^[^aeiou]*$")
SUFIJOS_VERBO = ("n", "nku", "ni", "nki", "nchik", "nchis", "spa", "sqa", "chun", "rqa", "rqan", "nqa", "na", "q")
ARTICULOS = {"el", "la", "los", "las", "un", "una", "unos", "unas", "lo"}


def normal(texto: str) -> str:
    t = unicodedata.normalize("NFC", texto or "").lower()
    return t.replace("’", "'").replace("ʼ", "'").replace("´", "'").replace("‘", "'").strip()


def sin_tildes(texto: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn" or c == "̃")


def terminos(glosa: str) -> set[str]:
    salida = set()
    for p in re.split(r"[;,/]", re.sub(r"\([^)]*\)", "", normal(glosa))):
        t = " ".join(x for x in p.strip(" .¡!¿?\"«»").split() if x not in ARTICULOS)
        if t:
            salida.add(unicodedata.normalize("NFC", sin_tildes(t)))
    return salida


def clave_quechua(forma: str) -> str:
    return normal(forma).replace("e", "i").replace("o", "u")


def tokens(texto: str) -> list[str]:
    return re.findall(r"[a-zñáéíóúäëïöü']+", normal(texto))


def rasgo_qullaw(forma: str) -> str:
    for palabra in normal(forma).split():
        if AJENA.search(palabra.replace("ch", "")):
            continue
        if EYECTIVA.search(palabra):
            return "eyectiva"
        if ASPIRADA.search(palabra):
            return "aspirada"
        if PROGRESIVO_SHA.match(palabra):
            return "progresivo_sha"
    return ""


def andino_a_quechua(valor: str) -> str:
    t = normal(valor)
    for a, b in (("č", "ch"), ("λ", "ll"), ("š", "sh"), ("ř", "r"), ("χ", "q"), ("ġ", "q"), (".", ""), (":", ""), ("-", ""), ("+", "")):
        t = t.replace(a, b)
    return clave_quechua(t)


def andino_a_aimara(valor: str) -> str:
    t = normal(valor)
    for v, larga in (("a", "ä"), ("i", "ï"), ("u", "ü")):
        t = t.replace(v + ":", larga)
    t = re.sub(r"(?<![ptkqč])h", "j", t)
    for a, b in (("č", "ch"), ("λ", "ll"), ("x", "j"), ("χ", "x"), (".", ""), ("-", ""), ("+", "")):
        t = t.replace(a, b)
    return t


def leer_andino():
    ruta = crudo / "crossandean" / "forms.csv"
    if not ruta.exists():
        return []
    with ruta.open(encoding="utf-8") as h:
        return [r for r in csv.DictReader(h) if r["Form"] and not r["Form"].startswith(".")]


def glosas_andino() -> dict[str, str]:
    ruta = crudo / "crossandean" / "Heggarty-2005-150.tsv"
    if not ruta.exists():
        return {}
    with ruta.open(encoding="utf-8") as h:
        return {r["NUMBER"]: r["SPANISH"] for r in csv.DictReader(h, delimiter="\t")}


def formas_puno() -> set[str]:
    ruta = curado / "puno_formas.csv"
    if not ruta.exists():
        return set()
    with ruta.open(encoding="utf-8") as h:
        return {clave_quechua(r["forma"]) for r in csv.DictReader(h)}


def variantes_quechua(forma: str) -> list[str]:
    k = clave_quechua(forma)
    salida = [k]
    if k.endswith("y") and len(k) > 4 and " " not in k:
        salida.append(k[:-1])
    return salida


def variantes_aimara(forma: str) -> list[str]:
    f = normal(forma)
    salida = [f]
    if f.endswith("ña") and len(f) > 4 and " " not in f:
        salida.append(f[:-2])
    return salida


class Clasificador:
    def __init__(self):
        self.qullaw = defaultdict(set)
        self.chanka = defaultdict(set)
        self.andino = defaultdict(list)
        self.aimara_andino = defaultdict(list)
        for forma in formas_puno():
            self.qullaw[forma].add("commonvoice_qxp")
        espanol = glosas_andino()
        aimara = defaultdict(lambda: {"norte": set(), "sur": set()})
        for r in leer_andino():
            numero = r["Parameter_ID"].split("_")[0]
            conceptos = terminos(espanol.get(numero, ""))
            lengua = r["Language_ID"]
            if lengua in ANDINO_QULLAW:
                self.andino[andino_a_quechua(r["Form"])].append(("qullaw", conceptos))
            elif lengua in ANDINO_CHANKA:
                self.andino[andino_a_quechua(r["Form"])].append(("chanka", conceptos))
            elif lengua == ANDINO_NORTE:
                aimara[numero]["norte"].add(andino_a_aimara(r["Form"]))
            elif lengua == ANDINO_SUR:
                aimara[numero]["sur"].add(andino_a_aimara(r["Form"]))
        for numero, d in aimara.items():
            if not (d["norte"] and d["sur"]):
                continue
            conceptos = terminos(espanol.get(numero, ""))
            for f in d["norte"] | d["sur"]:
                variedad = "comun" if f in d["norte"] and f in d["sur"] else "norte" if f in d["norte"] else "sur"
                self.aimara_andino[f].append((variedad, conceptos))

    def atestiguar_corpus(self, texto: str, variedad: str, origen: str):
        destino = self.qullaw if variedad == "qullaw" else self.chanka
        for t in tokens(texto):
            if variedad == "chanka" and rasgo_qullaw(t):
                continue
            destino[clave_quechua(t)].add(origen)

    def atestiguar_forma(self, forma: str, iso: str, origen: str):
        if iso in ISO_QULLAW:
            self.qullaw[clave_quechua(forma)].add(f"{origen}_{iso}")
        elif iso in ISO_CHANKA and not rasgo_qullaw(forma):
            self.chanka[clave_quechua(forma)].add(f"{origen}_{iso}")

    def _corpus(self, conjunto, forma: str) -> set[str]:
        k = clave_quechua(forma)
        origenes = set(conjunto.get(k, ()))
        if k.endswith("y") and len(k) > 4 and " " not in k:
            for s in SUFIJOS_VERBO:
                origenes |= conjunto.get(k[:-1] + s, set())
        return origenes

    def quechua(self, forma: str, iso: str, glosa: str = "") -> tuple[str, str]:
        rasgo = rasgo_qullaw(forma)
        if rasgo:
            return "qullaw", rasgo
        en_q = self._corpus(self.qullaw, forma)
        en_c = self._corpus(self.chanka, forma)
        sentidos = terminos(glosa)
        for k in variantes_quechua(forma):
            for variedad, conceptos in self.andino.get(k, ()):
                if conceptos & sentidos:
                    (en_q if variedad == "qullaw" else en_c).add("crossandean")
        if iso in ISO_QULLAW:
            en_q.add(f"iso_{iso}")
        if iso in ISO_CHANKA:
            en_c.add(f"iso_{iso}")
        if en_q and en_c:
            return "comun", "ambas:" + "+".join(sorted(en_q | en_c))
        if en_q:
            return "qullaw", "+".join(sorted(en_q))
        if en_c:
            return "chanka", "+".join(sorted(en_c))
        return "comun", "neutra"

    def aimara(self, forma: str, glosa: str = "") -> tuple[str, str]:
        sentidos = terminos(glosa)
        halladas = {v for k in variantes_aimara(forma) for v, conceptos in self.aimara_andino.get(k, ()) if conceptos & sentidos}
        if halladas == {"norte"}:
            return "norte", "crossandean_huancane"
        if halladas == {"sur"}:
            return "sur", "crossandean_sullkatiti"
        if halladas:
            return "comun", "ambas:crossandean"
        return "comun", "sin_atestiguar"

    def oracion_quechua(self, texto: str, declarada: str) -> tuple[str, str]:
        rasgos = [r for t in tokens(texto) if (r := rasgo_qullaw(t))]
        if declarada == "chanka":
            return ("", "mixta:" + rasgos[0]) if rasgos else ("chanka", "fuente_quy")
        if declarada == "qullaw":
            return "qullaw", "fuente_qullaw"
        if rasgos:
            return "qullaw", rasgos[0]
        return "", "sin_evidencia"


ETIQUETAS = {
    ("quechua", "qullaw"): "Quechua Qullaw (Collao)",
    ("quechua", "chanka"): "Quechua Chanka",
    ("quechua", "comun"): "Quechua sureño (común a Chanka y Qullaw)",
    ("aimara", "norte"): "Aimara norteño",
    ("aimara", "sur"): "Aimara sureño",
    ("aimara", "comun"): "Aimara (común)",
}
