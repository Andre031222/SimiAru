import gzip
import json
import sys
import tarfile
import time
import urllib.parse
import urllib.request
from pathlib import Path

raiz = Path(__file__).resolve().parents[1] / "fuentes" / "crudo"

americasnlp = "https://raw.githubusercontent.com/AmericasNLP/americasnlp2021/main/data"
tatoeba = "https://downloads.tatoeba.org/exports/per_language"
lexibank = "https://raw.githubusercontent.com/lexibank"
concepticon = "https://raw.githubusercontent.com/concepticon/concepticon-data/master/concepticondata/conceptlists"

descargas = {
    "eswiktionary-raw.jsonl.gz": "https://kaikki.org/eswiktionary/raw-wiktextract-data.jsonl.gz",
    "kaikki-enwiktionary-quechua/kaikki.org-dictionary-Quechua.jsonl": "https://kaikki.org/dictionary/Quechua/kaikki.org-dictionary-Quechua.jsonl",
    "americasnlp/quechua-spanish_README.md": f"{americasnlp}/quechua-spanish/README.md",
    "americasnlp/quechua-spanish_dev.quy": f"{americasnlp}/quechua-spanish/dev.quy",
    "americasnlp/quechua-spanish_dev.es": f"{americasnlp}/quechua-spanish/dev.es",
    "americasnlp/aymara-spanish_README.md": f"{americasnlp}/aymara-spanish/README.md",
    "americasnlp/aymara-spanish_dev.aym": f"{americasnlp}/aymara-spanish/dev.aym",
    "americasnlp/aymara-spanish_dev.es": f"{americasnlp}/aymara-spanish/dev.es",
    "americasnlp/aymara-spanish_train.aym": f"{americasnlp}/aymara-spanish/train.aym",
    "americasnlp/aymara-spanish_train.es": f"{americasnlp}/aymara-spanish/train.es",
    "flores200/flores200_dataset.tar.gz": "https://dl.fbaipublicfiles.com/nllb/flores200_dataset.tar.gz",
    "tatoeba/que_sentences_detailed.tsv.bz2": f"{tatoeba}/que/que_sentences_detailed.tsv.bz2",
    "tatoeba/aym_sentences_detailed.tsv.bz2": f"{tatoeba}/aym/aym_sentences_detailed.tsv.bz2",
    "tatoeba/que-spa_links.tsv.bz2": f"{tatoeba}/que/que-spa_links.tsv.bz2",
    "tatoeba/aym-spa_links.tsv.bz2": f"{tatoeba}/aym/aym-spa_links.tsv.bz2",
    "tatoeba/spa_sentences.tsv.bz2": f"{tatoeba}/spa/spa_sentences.tsv.bz2",
    "ids/languages.csv": f"{lexibank}/ids/master/cldf/languages.csv",
    "ids/parameters.csv": f"{lexibank}/ids/master/cldf/parameters.csv",
    "ids/forms.csv": f"{lexibank}/ids/master/cldf/forms.csv",
    "ids/metadata.json": f"{lexibank}/ids/master/metadata.json",
    "ids/Key-2016-1310.tsv": f"{concepticon}/Key-2016-1310.tsv",
    "crossandean/languages.csv": f"{lexibank}/crossandean/main/cldf/languages.csv",
    "crossandean/parameters.csv": f"{lexibank}/crossandean/main/cldf/parameters.csv",
    "crossandean/forms.csv": f"{lexibank}/crossandean/main/cldf/forms.csv",
    "crossandean/metadata.json": f"{lexibank}/crossandean/main/metadata.json",
    "crossandean/Heggarty-2005-150.tsv": f"{concepticon}/Heggarty-2005-150.tsv",
}

traducciones_en = "https://kaikki.org/dictionary/English/kaikki.org-dictionary-English.jsonl.gz"
codigos_traduccion = {"es", "qu", "quz", "quy", "qxp", "quh", "ay", "ayr", "aym"}


def descargar(destino: Path, url: str) -> None:
    if destino.exists() and destino.stat().st_size > 0:
        print(f"existe  {destino.relative_to(raiz)}")
        return
    destino.parent.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(url, destino)
    print(f"descargado  {destino.relative_to(raiz)}")


agente = {"User-Agent": "eLOP/1.0 (academic research; Universidad Nacional del Altiplano, Puno)"}

consulta_lexemas = """
SELECT ?l ?lemma ?catLabel ?sense ?gloss_es ?gloss_en ?item ?itemLabel_es ?trad_es WHERE {
  ?l dct:language wd:%s ; wikibase:lemma ?lemma ; wikibase:lexicalCategory ?cat .
  OPTIONAL { ?cat rdfs:label ?catLabel FILTER(lang(?catLabel) = "es") }
  OPTIONAL {
    ?l ontolex:sense ?sense .
    OPTIONAL { ?sense skos:definition ?gloss_es FILTER(lang(?gloss_es) = "es") }
    OPTIONAL { ?sense skos:definition ?gloss_en FILTER(lang(?gloss_en) = "en") }
    OPTIONAL { ?sense wdt:P5137 ?item . ?item rdfs:label ?itemLabel_es FILTER(lang(?itemLabel_es) = "es") }
    OPTIONAL { ?sense wdt:P5972 ?sentido_es . ?lex_es ontolex:sense ?sentido_es ; dct:language wd:Q1321 ; wikibase:lemma ?trad_es }
  }
}"""

categorias_audio = {
    "manifest_linguelibre_que_qxp.json": ["Category:Lingua Libre pronunciation-qxp", "Category:Lingua Libre pronunciation-que"],
    "manifest_linguelibre_quz.json": ["Category:Lingua Libre pronunciation-quz"],
    "manifest_linguelibre_quy.json": ["Category:Lingua Libre pronunciation-quy"],
    "manifest_linguelibre_quh.json": ["Category:Lingua Libre pronunciation-quh"],
    "manifest_aymara.json": ["Category:Aymara pronunciation"],
}


def obtener_json(url: str, datos: bytes | None = None) -> dict:
    peticion = urllib.request.Request(url, data=datos, headers={**agente, "Accept": "application/sparql-results+json, application/json"})
    with urllib.request.urlopen(peticion, timeout=300) as r:
        return json.load(r)


def descargar_wikidata(carpeta: Path) -> None:
    for qid in ("Q5218", "Q4627"):
        destino = carpeta / f"lexemes_{qid}.json"
        if destino.exists():
            print(f"existe  wikidata/{destino.name}")
            continue
        carpeta.mkdir(parents=True, exist_ok=True)
        datos = urllib.parse.urlencode({"query": consulta_lexemas % qid, "format": "json"}).encode()
        destino.write_text(json.dumps(obtener_json("https://query.wikidata.org/sparql", datos), ensure_ascii=False), encoding="utf-8")
        print(f"descargado  wikidata/{destino.name}")


def miembros(categoria: str) -> list[str]:
    titulos, continuar = [], {}
    while True:
        parametros = {"action": "query", "list": "categorymembers", "cmtitle": categoria, "cmtype": "file",
                      "cmlimit": "500", "format": "json", **continuar}
        r = obtener_json("https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(parametros))
        titulos += [m["title"] for m in r.get("query", {}).get("categorymembers", [])]
        if "continue" not in r:
            return titulos
        continuar = r["continue"]


def informacion(titulos: list[str], categoria: str) -> list[dict]:
    registros = []
    for i in range(0, len(titulos), 50):
        parametros = {"action": "query", "titles": "|".join(titulos[i:i + 50]), "prop": "imageinfo",
                      "iiprop": "url|size|mime|extmetadata", "format": "json"}
        r = obtener_json("https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(parametros))
        for pagina in r.get("query", {}).get("pages", {}).values():
            info = (pagina.get("imageinfo") or [{}])[0]
            meta = info.get("extmetadata", {})
            registros.append({
                "title": pagina.get("title", ""), "category": categoria, "url": info.get("url", ""),
                "size": info.get("size", 0), "mime": info.get("mime", ""),
                "license": meta.get("LicenseShortName", {}).get("value", ""),
                "license_url": meta.get("LicenseUrl", {}).get("value", ""),
                "artist": meta.get("Artist", {}).get("value", ""),
            })
        time.sleep(0.5)
    return registros


def descargar_manifiestos(carpeta: Path) -> None:
    for archivo, categorias in categorias_audio.items():
        destino = carpeta / archivo
        if destino.exists():
            print(f"existe  wikimedia-commons-audio/{archivo}")
            continue
        carpeta.mkdir(parents=True, exist_ok=True)
        registros = [r for c in categorias for r in informacion(miembros(c), c)]
        destino.write_text(json.dumps(registros, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"descargado  wikimedia-commons-audio/{archivo} ({len(registros)} archivos)")


def extraer_flores() -> None:
    carpeta = raiz / "flores200"
    if not (carpeta / "flores200_dataset").exists():
        with tarfile.open(carpeta / "flores200_dataset.tar.gz") as tar:
            miembros_tar = [m for m in tar.getmembers() if any(c in m.name for c in ("spa_Latn", "quy_Latn", "ayr_Latn", "README", "metadata"))]
            tar.extractall(carpeta, members=miembros_tar, filter="data")


def traducciones(d: dict) -> list[dict]:
    lista = list(d.get("translations", []))
    for s in d.get("senses", []):
        lista += s.get("translations", [])
    return [
        {k: t.get(k) for k in ("code", "word", "sense", "tags", "roman") if t.get(k)}
        for t in lista
        if (t.get("code") or t.get("lang_code")) in codigos_traduccion and t.get("word")
    ]


def descargar_traducciones_en(carpeta: Path) -> None:
    destino = carpeta / "traducciones-es-qu-ay.jsonl"
    if destino.exists() and destino.stat().st_size > 0:
        print(f"existe  {destino.relative_to(raiz)}")
        return
    carpeta.mkdir(parents=True, exist_ok=True)
    temporal = destino.with_suffix(".parcial")
    peticion = urllib.request.Request(traducciones_en, headers=agente)
    entradas = 0
    with urllib.request.urlopen(peticion, timeout=600) as r, gzip.open(r, "rt", encoding="utf-8") as g, temporal.open("w", encoding="utf-8") as h:
        for linea in g:
            if '"qu"' not in linea and '"ay"' not in linea:
                continue
            d = json.loads(linea)
            lista = traducciones(d)
            codigos = {t["code"] for t in lista}
            if "es" in codigos and codigos - {"es"}:
                h.write(json.dumps({"word": d.get("word"), "pos": d.get("pos"), "translations": lista}, ensure_ascii=False) + "\n")
                entradas += 1
    temporal.rename(destino)
    (carpeta / "ORIGEN.txt").write_text(
        f"Extracto de {traducciones_en} (wiktextract, Wiktionary en inglés, CC BY-SA 4.0).\n"
        f"Solo entradas con traducción al español y al quechua o aimara en la misma tabla.\n"
        f"Fecha de acceso: {time.strftime('%Y-%m-%d')}. Entradas: {entradas}.\n",
        encoding="utf-8",
    )
    print(f"descargado  {destino.relative_to(raiz)} ({entradas} entradas)")


if __name__ == "__main__":
    pasos = set(sys.argv[1:])
    if not pasos or "basicas" in pasos:
        for nombre, url in descargas.items():
            descargar(raiz / nombre, url)
        extraer_flores()
        descargar_wikidata(raiz / "wikidata")
        descargar_manifiestos(raiz / "wikimedia-commons-audio")
    if not pasos or "traducciones" in pasos:
        descargar_traducciones_en(raiz / "kaikki-enwiktionary-traducciones")
