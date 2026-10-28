# /// script
# requires-python = ">=3.11"
# dependencies = ["wordfreq>=3.1"]
# ///
import bz2
import csv
import json
import re
import sqlite3
import unicodedata
from collections import Counter
from pathlib import Path

from wordfreq import zipf_frequency

raiz = Path(__file__).resolve().parents[2]
curado = raiz / "datos" / "curado"
crudo = raiz / "datos" / "fuentes" / "crudo"
base = curado / "tinku-contenido.sqlite"

MINIMO_APTA = 1.2
MINIMO_NUCLEO = 3.6
VACIAS = {"de", "la", "el", "los", "las", "un", "una", "a", "en", "con", "por", "para", "se", "que", "y", "o", "al", "del", "lo", "su", "sus", "algo", "alguien"}
LARGAS = (("aa", "ä"), ("ii", "ï"), ("uu", "ü"))


def normal(texto: str) -> str:
    t = unicodedata.normalize("NFC", texto.lower())
    for a in ("’", "‘", "´", "`", "ʼ"):
        t = t.replace(a, "'")
    return t


def fichas(texto: str) -> list[str]:
    return re.findall(r"[a-zñäïü']+", normal(texto))


def corpus_wikipedia(nombre: str) -> Counter:
    ruta = crudo / "wikipedia" / f"{nombre}.xml.bz2"
    cuenta: Counter = Counter()
    if not ruta.exists():
        return cuenta
    with bz2.open(ruta, "rt", encoding="utf-8") as h:
        contenido = h.read()
    for pagina in re.finditer(r"<ns>0</ns>.*?<text[^>]*>(.*?)</text>", contenido, re.S):
        texto = pagina.group(1)
        texto = re.sub(r"\{\{.*?\}\}", " ", texto, flags=re.S)
        texto = re.sub(r"\[\[(?:[^\]|]*\|)?([^\]]*)\]\]", r"\1", texto)
        texto = re.sub(r"&lt;.*?&gt;|<[^>]+>|\[https?://\S+|https?://\S+", " ", texto)
        cuenta.update(t.strip("'") for t in fichas(texto))
    return cuenta


def corpus_puno() -> Counter:
    cuenta: Counter = Counter()
    ruta = curado / "puno_formas.csv"
    if ruta.exists():
        with ruta.open(encoding="utf-8") as h:
            for f in csv.DictReader(h):
                cuenta[normal(f["forma"])] += int(f["frecuencia"] or 0)
    return cuenta


def cabeza(glosa: str) -> list[str]:
    pieza = re.split(r"[;,(]", glosa or "")[0].strip().lower()
    return [p for p in re.findall(r"[a-záéíóúñü]+", pieza) if p not in VACIAS]


def frecuencia_es(glosa: str) -> float:
    valores = []
    for pieza in re.split(r"[;,]", re.sub(r"\([^)]*\)", "", glosa or ""))[:3]:
        palabras = cabeza(pieza)
        if palabras:
            valores.append(min(zipf_frequency(p, "es") for p in palabras[:2]))
    return max(valores, default=0.0)


def ortografia(lengua: str, forma: str) -> str:
    completa = normal(forma)
    f = completa.replace("ch", "")
    if lengua == "quechua":
        if re.search(r"[bcdfgjvxz]", f):
            return "letra_ajena"
        if re.search(r"(aa|ii|uu)", completa):
            return "vocal_larga_no_surena"
        if re.search(r"[eo]", f):
            return "ortografia_pentavocal"
        return ""
    if re.search(r"[bcdfgvz]", f):
        return "letra_ajena"
    if re.search(r"[eo]", completa):
        return "ortografia_pentavocal"
    return ""


def uso(forma: str, corpus: Counter) -> int:
    partes = [p.strip("'") for p in fichas(forma)]
    if not partes:
        return 0
    return min(corpus.get(p, 0) for p in partes)


def main():
    wiki_qu = corpus_wikipedia("quwiki")
    wiki_ay = corpus_wikipedia("aywiki")
    puno = corpus_puno()
    db = sqlite3.connect(base)
    db.row_factory = sqlite3.Row
    columnas = {r[1] for r in db.execute("pragma table_info(lexico)")}
    for col, tipo in (("frecuencia_es", "real default 0"), ("uso_corpus", "integer default 0"), ("nucleo", "integer default 0"), ("motivo_calidad", "text default ''")):
        if col not in columnas:
            db.execute(f"alter table lexico add column {col} {tipo}")
    filas = [dict(r) for r in db.execute("select id, lengua, forma, glosa_es, fuente_id, confianza, soporte, apta from lexico")]
    informe: Counter = Counter()
    ejemplos: dict[str, list[str]] = {}
    cambios = []
    for f in filas:
        forma = f["forma"]
        if f["lengua"] == "aimara" and f["fuente_id"] == "ids":
            for a, b in LARGAS:
                forma = forma.replace(a, b)
        motivo = ortografia(f["lengua"], forma)
        if not motivo and forma.startswith("-"):
            motivo = "sufijo"
        zipf = frecuencia_es(f["glosa_es"])
        if not motivo and zipf < MINIMO_APTA:
            motivo = "glosa_rara"
        corpus = wiki_qu + puno if f["lengua"] == "quechua" else wiki_ay
        n_uso = uso(forma, corpus)
        apta = int(bool(f["apta"]) and not motivo)
        respaldo = (f["confianza"] or 0) >= 3 or (f["soporte"] or 0) >= 3 or n_uso >= 3
        nucleo = int(apta and zipf >= MINIMO_NUCLEO and respaldo)
        clave = f"{f['lengua']}:{motivo or ('nucleo' if nucleo else 'apta' if apta else 'no_apta')}"
        informe[clave] += 1
        if len(ejemplos.setdefault(clave, [])) < 12:
            ejemplos[clave].append(f"{forma} = {f['glosa_es'][:40]}")
        cambios.append((forma, round(zipf, 2), n_uso, nucleo, motivo, apta, f["id"]))
    db.executemany("update lexico set forma = ?, frecuencia_es = ?, uso_corpus = ?, nucleo = ?, motivo_calidad = ?, apta = ? where id = ?", cambios)
    db.commit()
    resumen = {
        "minimo_apta_zipf": MINIMO_APTA,
        "minimo_nucleo_zipf": MINIMO_NUCLEO,
        "corpus": {"quwiki_fichas": sum(wiki_qu.values()), "aywiki_fichas": sum(wiki_ay.values()), "puno_fichas": sum(puno.values())},
        "conteos": dict(sorted(informe.items())),
        "ejemplos": ejemplos,
    }
    (curado / "calidad-lexica.json").write_text(json.dumps(resumen, ensure_ascii=False, indent=2), encoding="utf-8")
    cols = [r[1] for r in db.execute("pragma table_info(lexico)")]
    with (curado / "lexico.csv").open("w", encoding="utf-8", newline="") as h:
        w = csv.writer(h)
        w.writerow(cols)
        w.writerows(db.execute(f"select {', '.join(cols)} from lexico order by id"))
    print(json.dumps(resumen["conteos"], ensure_ascii=False, indent=1))
    print(resumen["corpus"])


if __name__ == "__main__":
    main()
