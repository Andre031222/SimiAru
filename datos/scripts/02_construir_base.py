import bz2
import csv
import gzip
import json
import re
import sqlite3
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from variedades import ETIQUETAS, Clasificador

datos = Path(__file__).resolve().parents[1]
crudo = datos / "fuentes" / "crudo"
curado = datos / "curado"
anlp = crudo / "americasnlp"

lengua_de = {"quy": "quechua", "quz": "quechua", "quh": "quechua", "qu": "quechua", "ay": "aimara", "ayr": "aimara"}
etiquetas_no_sureno = {"Ecuador", "Huallaga", "Ancash", "Ancash Quechua", "Junín", "Kichwa", "Santiago del Estero", "Colombia"}
etiquetas_qullaw = {"Cusco": "quz", "Bolivia": "quh", "Puno": "quz"}
etiquetas_es_excluidas = {"colloquial", "slang", "vulgar", "archaic", "obsolete", "dated", "rare", "derogatory", "offensive", "Spain"}

fuentes = [
    {
        "id": "wikcionario_es",
        "nombre": "Wikcionario en español (extracción wiktextract / Kaikki.org)",
        "tipo": "diccionario",
        "lenguas": "quz, quy, quh, qu, ay, es",
        "url": "https://kaikki.org/eswiktionary/",
        "licencia": "CC BY-SA 4.0",
        "redistribuible": "sí, con atribución y misma licencia",
        "cita": "ylonen2022wiktextract",
    },
    {
        "id": "wikcionario_en",
        "nombre": "Wiktionary en inglés: tablas de traducción con español y quechua o aimara en la misma acepción (wiktextract / Kaikki.org)",
        "tipo": "diccionario",
        "lenguas": "qu, ay, es",
        "url": "https://kaikki.org/dictionary/English/",
        "licencia": "CC BY-SA 4.0",
        "redistribuible": "sí, con atribución y misma licencia",
        "cita": "ylonen2022wiktextract",
    },
    {
        "id": "wikidata_lexemas",
        "nombre": "Lexemas de Wikidata en quechua y aimara",
        "tipo": "léxico",
        "lenguas": "qu, ay, es",
        "url": "https://www.wikidata.org/wiki/Wikidata:Lexicographical_data",
        "licencia": "CC0 1.0",
        "redistribuible": "sí",
        "cita": "vrandecic2014wikidata",
    },
    {
        "id": "ids",
        "nombre": "Intercontinental Dictionary Series (IDS), lista aimara de Félix Layme Pairumani, versión CLDF de Lexibank; glosas en español de la lista IDS en Concepticon",
        "tipo": "lista léxica",
        "lenguas": "ayr, es",
        "url": "https://ids.clld.org/contributions/269",
        "licencia": "CC BY 4.0",
        "redistribuible": "sí, con atribución",
        "cita": "key2023ids",
    },
    {
        "id": "crossandean",
        "nombre": "Blum et al. (2023), lista comparativa andina (CLDF, Lexibank): aimara de Huancané y de Sullkatiti; quechua de Ayacucho, Huancavelica, Puno, Cuzco y otras localidades; glosas en español de la lista de Heggarty (2005) en Concepticon. Solo como evidencia de variedad",
        "tipo": "evidencia de variedad",
        "lenguas": "ayr, quy, quz, qxp, quh, es",
        "url": "https://github.com/lexibank/crossandean",
        "licencia": "CC BY 4.0",
        "redistribuible": "sí, con atribución",
        "cita": "blum2023quechua",
    },
    {
        "id": "americasnli",
        "nombre": "AmericasNLI: oraciones XNLI traducidas por hablantes a quechua y aimara",
        "tipo": "corpus paralelo",
        "lenguas": "es, quy, aym",
        "url": "https://github.com/abteen/americasnli",
        "licencia": "CC BY-SA 4.0",
        "redistribuible": "sí, con atribución y misma licencia",
        "cita": "ebrahimi2022americasnli",
    },
    {
        "id": "globalvoices_opus",
        "nombre": "Global Voices español–aimara (OPUS), distribuido por AmericasNLP 2021",
        "tipo": "corpus paralelo",
        "lenguas": "es, aym",
        "url": "https://opus.nlpl.eu/GlobalVoices.php",
        "licencia": "CC BY 3.0 (Global Voices)",
        "redistribuible": "sí, con atribución",
        "cita": "tiedemann2012opus",
    },
    {
        "id": "flores200",
        "nombre": "FLORES-200 (NLLB), conjunto dev; devtest reservado para evaluación",
        "tipo": "corpus paralelo",
        "lenguas": "spa, quy, ayr",
        "url": "https://github.com/facebookresearch/flores",
        "licencia": "CC BY-SA 4.0",
        "redistribuible": "sí, con atribución y misma licencia",
        "cita": "nllb2022",
    },
    {
        "id": "tatoeba",
        "nombre": "Tatoeba: oraciones en quechua y aimara con traducción al español",
        "tipo": "corpus paralelo",
        "lenguas": "que, aym, es",
        "url": "https://tatoeba.org/",
        "licencia": "CC BY 2.0 FR",
        "redistribuible": "sí, con atribución",
        "cita": "tatoeba",
    },
    {
        "id": "dudh",
        "nombre": "Declaración Universal de Derechos Humanos (español, quechua cuzqueño, ayacuchano y boliviano, aimara), recopilada en AmericasNLP 2024",
        "tipo": "texto oficial paralelo",
        "lenguas": "es, quz, quy, quh, aym",
        "url": "https://www.ohchr.org/en/human-rights/universal-declaration/universal-declaration-human-rights/about-universal-declaration-human-rights-translation-project",
        "licencia": "texto de libre reproducción (ONU)",
        "redistribuible": "sí, citando la fuente",
        "cita": "degibert2023four",
    },
    {
        "id": "constituciones",
        "nombre": "Constituciones Políticas del Perú y de Bolivia en quechua y aimara, recopiladas en AmericasNLP 2024",
        "tipo": "texto oficial paralelo",
        "lenguas": "es, que, quh, aym",
        "url": "https://github.com/AmericasNLP/americasnlp2024",
        "licencia": "texto legal oficial, excluido de la protección del derecho de autor (D. Leg. 822, art. 9, Perú)",
        "redistribuible": "sí, citando la fuente",
        "cita": "degibert2023four",
    },
    {
        "id": "lingua_libre",
        "nombre": "Grabaciones de hablantes en Lingua Libre y Wikimedia Commons",
        "tipo": "audio de hablantes",
        "lenguas": "qxp, quz, quy, quh, ay",
        "url": "https://lingualibre.org/",
        "licencia": "CC BY-SA 4.0, CC BY 4.0 o CC0 según grabación",
        "redistribuible": "sí, con atribución a cada hablante",
        "cita": "lingualibre",
    },
]

fuentes_por_id = {f["id"]: f for f in fuentes}
confianza = {"wikcionario_es": 3, "ids": 3, "wikidata_lexemas": 2, "wikcionario_en": 2}

temas = {
    "saludos": ("A1", "saludo saludos hola adiós gracias buenos buenas días tardes noches perdón bienvenido favor disculpa"),
    "numeros": ("A1", "uno dos tres cuatro cinco seis siete ocho nueve diez once doce veinte treinta cien ciento mil número cero primero segundo tercero mitad"),
    "familia": ("A1", "padre madre papá mamá hijo hija hermano hermana abuelo abuela tío tía esposo esposa yerno nuera nieto nieta primo prima familia bebé niño niña suegro suegra cuñado cuñada huérfano"),
    "cuerpo": ("A1", "cabeza ojo ojos boca nariz oreja mano manos pie pies brazo pierna diente dientes lengua cabello pelo corazón estómago espalda dedo uña cuello rodilla hueso sangre piel cara frente hombro barriga labio ceja pecho hígado"),
    "colores": ("A1", "rojo blanco negro azul verde amarillo color gris morado celeste marrón pardo colorado anaranjado rosado"),
    "animales": ("A1", "perro gato llama alpaca vicuña vaca toro oveja cerdo chancho caballo burro gallina gallo pájaro ave cóndor zorro ratón rata pez sapo culebra serpiente insecto pulga piojo mosca hormiga cuy vizcacha puma oso animal perdiz paloma picaflor mariposa araña gusano liendre cordero ternero pato halcón águila lagarto"),
    "comida": ("A1", "papa maíz quinua pan carne leche comida comer sal ají chuño queso huevo sopa fruta harina arroz frijol haba oca olluco chicha trigo cebada mote tostado desayuno almuerzo cena mazamorra charqui"),
    "naturaleza": ("A2", "sol luna estrella cielo lluvia nieve granizo helada viento nube río lago mar cerro montaña piedra tierra fuego árbol flor planta hierba pasto campo agua bosque laguna nevado arcoíris trueno rayo relámpago arena barro"),
    "hogar": ("A2", "casa puerta techo pared cocina olla plato cuchara cama cuarto ventana mesa silla fogón vasija cántaro patio corral canasta"),
    "vestido": ("A2", "ropa poncho sombrero chompa pantalón falda pollera manta lliclla sandalia ojota tejido tejer lana hilo aguja chullo camisa vestido"),
    "tiempo": ("A2", "día noche mañana tarde hoy ayer año mes semana hora tiempo temprano siempre nunca ahora antes después invierno verano lunes martes miércoles jueves viernes sábado domingo"),
    "comunidad": ("A2", "pueblo ciudad comunidad camino escuela mercado iglesia plaza chacra ayllu tierra calle puente país región fiesta feria"),
    "personas": ("A2", "hombre mujer persona gente joven anciano viejo maestro profesor doctor médico curandero pastor agricultor autoridad amigo amiga vecino vecina señor señora jefe"),
    "acciones": ("A2", "ir venir comer beber tomar dormir caminar correr hablar decir ver mirar oír escuchar trabajar cantar bailar llorar reír escribir leer abrir cerrar dar recibir hacer sembrar cosechar cocinar lavar vivir morir saber conocer querer amar buscar encontrar llevar traer subir bajar entrar salir sentarse pararse jugar pensar"),
    "cualidades": ("B1", "grande pequeño alto bajo bueno malo nuevo viejo bonito hermoso feo largo corto caliente frío dulce amargo agrio salado lleno vacío fuerte débil rápido lento limpio sucio rico pobre gordo flaco duro blando"),
    "emociones": ("B1", "alegre alegría triste tristeza enojo enojado miedo cariño amor pena contento feliz vergüenza preocupado cansado"),
}

palabra_tema = {}
for tema, (_, lista) in temas.items():
    for palabra in lista.split():
        palabra_tema.setdefault(palabra, tema)

articulos = {"el", "la", "los", "las", "un", "una", "unos", "unas", "lo"}
alfabeto = set("abcdefghijklmnñopqrstuvwxyzäïü' -")


def leer_correcciones():
    ruta = datos / "fuentes" / "correcciones-glosas.csv"
    if not ruta.exists():
        return {}
    with ruta.open(encoding="utf-8") as f:
        return {(r["lengua"], r["forma"].lower(), r["glosa_original"].lower()): r for r in csv.DictReader(f)}


correcciones = leer_correcciones()


def ortografia_valida(forma: str, lengua: str) -> bool:
    f = forma.lower()
    if not f or any(c not in alfabeto for c in f):
        return False
    if re.search(r"c(?!h)", f):
        return False
    if lengua == "quechua" and "x" in f:
        return False
    if lengua == "aimara" and re.search(r"[eobdfgv]", f):
        return False
    return True


def limpiar(texto: str) -> str:
    texto = unicodedata.normalize("NFC", texto or "").replace("ʼ", "'").replace("’", "'")
    texto = texto.replace("​", "").strip().strip("“”\"")
    texto = re.sub(r"!{2,}", "", texto)
    texto = re.sub(r"\s+", " ", texto)
    texto = re.sub(r"'{2,}", "'", texto)
    return texto.rstrip(".").strip()


def clave(glosa: str) -> str:
    g = limpiar(glosa).lower()
    g = re.split(r"[;,(]| o | / ", g)[0].strip(" .¡!¿?")
    tokens = [t for t in g.split() if t not in articulos]
    if not tokens or len(tokens) > 3:
        return ""
    return " ".join(tokens)


def terminos(glosa: str) -> list[str]:
    salida = []
    for p in re.split(r"[;,]| / ", re.sub(r"\([^)]*\)", "", glosa.lower())):
        t = " ".join(x for x in p.strip(" .¡!¿?\"«»").split() if x not in articulos)
        if t and t not in salida:
            salida.append(t)
    return salida


def tema_de(glosa: str) -> str:
    for token in re.findall(r"[a-záéíóúñü]+", glosa.lower())[:4]:
        if token in palabra_tema:
            return palabra_tema[token]
    return "general"


def nivel_de(tema: str, forma: str) -> str:
    if tema in temas:
        return temas[tema][0]
    return "B1" if len(forma.split()) == 1 else "B2"


def nivel_oracion(texto: str) -> str:
    n = len(texto.split())
    if n <= 6:
        return "A2"
    if n <= 14:
        return "B1"
    return "B2"


def registro(codigo, forma, glosa, categoria="", ipa="", ejemplo="", ejemplo_es="", fuente_url=""):
    return {"codigo": codigo, "forma": forma, "glosa_es": glosa, "categoria": categoria, "ipa": ipa,
            "ejemplo": ejemplo, "ejemplo_es": ejemplo_es, "fuente_url": fuente_url}


def leer_wikcionario():
    entradas, traducciones = [], []
    with gzip.open(crudo / "eswiktionary-raw.jsonl.gz", "rt", encoding="utf-8") as f:
        for linea in f:
            d = json.loads(linea)
            codigo = d.get("lang_code")
            if codigo in lengua_de:
                ipa = next((s["ipa"] for s in d.get("sounds", []) if "ipa" in s), "")
                for sentido in d.get("senses", []):
                    glosas = [limpiar(g) for g in sentido.get("glosses", []) if limpiar(g)]
                    if not glosas:
                        continue
                    ejemplo = next((limpiar(e.get("text", "")) for e in sentido.get("examples", [])), "")
                    entradas.append(registro(codigo, limpiar(d["word"]), glosas[0], d.get("pos_title", d.get("pos", "")), ipa, ejemplo, "",
                                             f"https://es.wiktionary.org/wiki/{d['word'].replace(' ', '_')}"))
            elif codigo == "es":
                for t in d.get("translations", []):
                    tc = t.get("lang_code")
                    if tc in lengua_de and t.get("word"):
                        traducciones.append(registro(tc, limpiar(t["word"]), limpiar(d["word"]), d.get("pos_title", d.get("pos", "")), "", "", "",
                                                     f"https://es.wiktionary.org/wiki/{d['word'].replace(' ', '_')}#Traducciones"))
    return entradas + traducciones


def leer_wikidata():
    salida = []
    for archivo, codigo in (("lexemes_Q4627.json", "ay"), ("lexemes_Q5218.json", "qu")):
        datos_json = json.loads((crudo / "wikidata" / archivo).read_text(encoding="utf-8"))
        for b in datos_json.get("results", {}).get("bindings", []):
            glosa = (b.get("gloss_es") or b.get("trad_es") or b.get("itemLabel_es") or {}).get("value", "")
            lema = b.get("lemma", {}).get("value", "")
            if lema and glosa:
                salida.append(registro(codigo, limpiar(lema), limpiar(glosa), b.get("catLabel", {}).get("value", ""), fuente_url=b["l"]["value"]))
    return salida


def leer_wikcionario_en():
    ruta = crudo / "kaikki-enwiktionary-traducciones" / "traducciones-es-qu-ay.jsonl"
    salida = []
    if not ruta.exists():
        return salida
    with ruta.open(encoding="utf-8") as h:
        for linea in h:
            d = json.loads(linea)
            palabra = d.get("word") or ""
            if d.get("pos") == "name" or palabra[:1].isupper():
                continue
            por_sentido = defaultdict(list)
            for t in d["translations"]:
                por_sentido[t.get("sense", "")].append(t)
            for grupo in por_sentido.values():
                espanol = []
                for t in grupo:
                    if t["code"] == "es" and not set(t.get("tags", [])) & etiquetas_es_excluidas:
                        w = limpiar(re.sub(r"\([^)]*\)", "", t["word"]))
                        if w and w not in espanol and len(w.split()) <= 4 and not w[:1].isupper():
                            espanol.append(w)
                if not espanol:
                    continue
                for t in grupo:
                    if t["code"] not in ("qu", "ay"):
                        continue
                    etiquetas = set(t.get("tags", []))
                    if etiquetas & etiquetas_no_sureno:
                        continue
                    codigo = next((etiquetas_qullaw[e] for e in etiquetas if e in etiquetas_qullaw), t["code"])
                    salida.append(registro(codigo, limpiar(re.sub(r"\([^)]*\)", "", t["word"])), ", ".join(espanol[:3]),
                                           d.get("pos", ""), fuente_url=f"https://en.wiktionary.org/wiki/{palabra.replace(' ', '_')}#Translations"))
    return salida


def ids_a_aimara(valor: str) -> str:
    t = unicodedata.normalize("NFC", valor)
    for a, b in (("lʸ", "ll"), ("ḳ", "q"), ("č", "ch"), ("ˀ", "'"), ("ʰ", "h"), ("ɲ", "ñ"), ("x", "j"), ("χ", "x"),
                 ("aː", "ä"), ("iː", "ï"), ("uː", "ü"), ("-", ""), (" ", " ")):
        t = t.replace(a, b)
    return t.strip()


def leer_ids():
    base = crudo / "ids"
    if not (base / "forms.csv").exists():
        return []
    with (base / "Key-2016-1310.tsv").open(encoding="utf-8") as h:
        espanol = {r["IDS_ID"]: r["SPANISH"] for r in csv.DictReader(h, delimiter="\t")}
    salida = []
    with (base / "forms.csv").open(encoding="utf-8") as h:
        for r in csv.DictReader(h):
            if r["Language_ID"] != "269" or r["Value"].startswith("[") or "(" in r["Form"]:
                continue
            glosa = espanol.get(r["Parameter_ID"], "")
            if glosa:
                salida.append(registro("ayr", ids_a_aimara(r["Form"]), limpiar(glosa), fuente_url=f"https://ids.clld.org/values/{r['ID']}"))
    return salida


def leer_americasnlp2024():
    base = crudo / "americasnlp2024"
    filas = []
    tablas = defaultdict(dict)
    for lengua, carpeta in (("quechua", "quechua-spanish"), ("aimara", "aymara-spanish")):
        with (base / carpeta / "extra.tsv").open(encoding="utf-8") as f:
            for linea in f:
                partes = linea.rstrip("\n").split("\t")
                if len(partes) < 3:
                    continue
                origen, es, meta = partes[0].strip(), limpiar(partes[1]), limpiar(partes[2])
                if not es or not meta:
                    continue
                if lengua == "quechua" and origen == "udhr-quz":
                    tablas[("dudh", es)]["quechua"] = (meta, "qullaw")
                elif lengua == "aimara" and origen == "udhr":
                    tablas[("dudh", es)]["aimara"] = meta
                elif lengua == "quechua" and origen in ("udhr-quy", "udhr-quh"):
                    filas.append({"es": es, "quechua": meta, "aimara": "", "fuente_id": "dudh", "declarada": "chanka" if origen == "udhr-quy" else "qullaw",
                                  "licencia": fuentes_por_id["dudh"]["licencia"], "alineacion": "traduccion_oficial"})
                elif lengua == "quechua" and origen == "Bolivian_constitution":
                    tablas[("constituciones", es)]["quechua"] = (meta, "qullaw")
                elif lengua == "quechua" and origen == "Peruvian_constitution":
                    tablas[("constituciones", es)]["quechua"] = (meta, "")
                elif lengua == "aimara" and origen == "Bolivian_constitution":
                    tablas[("constituciones", es)]["aimara"] = meta
    for (fuente_id, es), d in tablas.items():
        quechua, declarada = d.get("quechua", ("", ""))
        filas.append({"es": es, "quechua": quechua, "aimara": d.get("aimara", ""), "fuente_id": fuente_id, "declarada": declarada,
                      "licencia": fuentes_por_id[fuente_id]["licencia"], "alineacion": "traduccion_oficial"})
    return filas


def leer_tatoeba():
    t = crudo / "tatoeba"
    textos = {}
    for archivo in ("que_sentences_detailed.tsv.bz2", "aym_sentences_detailed.tsv.bz2"):
        for linea in bz2.open(t / archivo, "rt", encoding="utf-8"):
            partes = linea.rstrip("\n").split("\t")
            textos[partes[0]] = (partes[1], partes[2])
    enlaces = []
    for archivo in ("que-spa_links.tsv.bz2", "aym-spa_links.tsv.bz2"):
        for linea in bz2.open(t / archivo, "rt", encoding="utf-8"):
            a, b = linea.split()
            enlaces.append((a, b))
    necesarios = {b for _, b in enlaces}
    espanol = {}
    for linea in bz2.open(t / "spa_sentences.tsv.bz2", "rt", encoding="utf-8"):
        partes = linea.rstrip("\n").split("\t")
        if partes[0] in necesarios:
            espanol[partes[0]] = partes[-1]
    filas = []
    for a, b in enlaces:
        if a in textos and b in espanol:
            lengua, texto = textos[a]
            filas.append({"es": limpiar(espanol[b]), "quechua": limpiar(texto) if lengua == "que" else "",
                          "aimara": limpiar(texto) if lengua == "aym" else "", "declarada": "",
                          "fuente_id": "tatoeba", "licencia": "CC BY 2.0 FR", "alineacion": "traduccion_colaborativa"})
    return filas


def leer_oraciones():
    filas = []
    qe = (anlp / "quechua-spanish_dev.es").read_text(encoding="utf-8").splitlines()
    qq = (anlp / "quechua-spanish_dev.quy").read_text(encoding="utf-8").splitlines()
    ae = (anlp / "aymara-spanish_dev.es").read_text(encoding="utf-8").splitlines()
    aa = (anlp / "aymara-spanish_dev.aym").read_text(encoding="utf-8").splitlines()
    aimara = dict(zip(ae, aa))
    for e, q in zip(qe, qq):
        if e in aimara:
            filas.append({"es": limpiar(e), "quechua": limpiar(q), "aimara": limpiar(aimara[e]), "declarada": "chanka",
                          "fuente_id": "americasnli", "licencia": "CC BY-SA 4.0", "alineacion": "traduccion_humana_trilingue"})
    flores = crudo / "flores200" / "flores200_dataset" / "dev"
    for e, q, a in zip(*[(flores / f"{c}_Latn.dev").read_text(encoding="utf-8").splitlines() for c in ("spa", "quy", "ayr")]):
        filas.append({"es": limpiar(e), "quechua": limpiar(q), "aimara": limpiar(a), "declarada": "chanka",
                      "fuente_id": "flores200", "licencia": "CC BY-SA 4.0", "alineacion": "traduccion_profesional_trilingue"})
    filas += leer_tatoeba()
    filas += leer_americasnlp2024()
    te = (anlp / "aymara-spanish_train.es").read_text(encoding="utf-8").splitlines()
    ta = (anlp / "aymara-spanish_train.aym").read_text(encoding="utf-8").splitlines()
    for e, a in zip(te, ta):
        e, a = limpiar(e), limpiar(a)
        if 3 <= len(e.split()) <= 30 and a:
            filas.append({"es": e, "quechua": "", "aimara": a, "declarada": "", "fuente_id": "globalvoices_opus",
                          "licencia": "CC BY 3.0", "alineacion": "alineacion_automatica_opus"})
    return filas


def preparar_clasificador(oraciones_crudas):
    c = Clasificador()
    for f in oraciones_crudas:
        if f["quechua"] and f["declarada"] in ("chanka", "qullaw"):
            c.atestiguar_corpus(f["quechua"], f["declarada"], f["fuente_id"])
    return c


def construir_lexico(clasificador):
    candidatos = []
    for fuente_id, lector in (("wikcionario_es", leer_wikcionario), ("wikidata_lexemas", leer_wikidata), ("ids", leer_ids),
                              ("wikcionario_en", leer_wikcionario_en)):
        for r in lector():
            candidatos.append((fuente_id, r))
    for fuente_id, r in candidatos:
        if lengua_de[r["codigo"]] == "quechua":
            clasificador.atestiguar_forma(r["forma"], r["codigo"], fuente_id)

    filas, vistos, apoyo = [], set(), set()
    for fuente_id, r in candidatos:
        forma = r["forma"]
        if not forma or len(forma) > 60:
            continue
        forma = forma[0].lower() + forma[1:] if forma[:1].isupper() and forma[1:].islower() else forma
        glosa = r["glosa_es"]
        glosa = glosa[0].lower() + glosa[1:] if glosa[:1].isupper() and len(glosa.split()) <= 4 else glosa
        lengua = lengua_de[r["codigo"]]
        if not ortografia_valida(forma, lengua):
            continue
        for t in terminos(glosa):
            apoyo.add((lengua, forma.lower(), t, fuente_id))
        llave = (lengua, forma.lower(), clave(glosa) or glosa.lower())
        if llave in vistos:
            continue
        vistos.add(llave)
        correccion = correcciones.get((lengua, forma.lower(), glosa.lower()))
        tema = correccion["tema"] if correccion else tema_de(glosa)
        if correccion:
            glosa = correccion["glosa_corregida"]
        if lengua == "quechua":
            variedad, evidencia = clasificador.quechua(forma, r["codigo"], glosa)
        else:
            variedad, evidencia = clasificador.aimara(forma, glosa)
        filas.append({
            "lengua": lengua,
            "iso": r["codigo"],
            "variante": ETIQUETAS[(lengua, variedad)],
            "variedad": variedad,
            "variedad_evidencia": evidencia,
            "forma": forma,
            "glosa_es": glosa,
            "concepto": clave(glosa),
            "categoria": r.get("categoria", ""),
            "tema": tema,
            "nivel": nivel_de(tema, forma),
            "ipa": r.get("ipa", ""),
            "ejemplo": r.get("ejemplo", ""),
            "ejemplo_es": r.get("ejemplo_es", ""),
            "fuente_id": fuente_id,
            "fuente_url": r["fuente_url"],
            "licencia": fuentes_por_id[fuente_id]["licencia"],
            "estado_revision": "corregida_equipo" if correccion else "fuente_publicada",
            "confianza": 2 if correccion else confianza[fuente_id],
            "registro": "|".join((*llave, fuente_id)),
        })
    filas.sort(key=lambda f: (f["lengua"], f["forma"].lower(), f["registro"]))
    asignar_ids(filas)
    return filas, sorted(apoyo)


def leer_mapa(ruta: Path, clave_col: str) -> dict:
    if not ruta.exists():
        return {}
    with ruta.open(encoding="utf-8") as f:
        return {r[clave_col]: r["id"] for r in csv.DictReader(f)}


def leer_ultimos() -> dict:
    ruta = curado / "ids-ultimo.csv"
    if not ruta.exists():
        return {}
    with ruta.open(encoding="utf-8") as f:
        return {r["prefijo"]: int(r["ultimo"]) for r in csv.DictReader(f)}


def escribir_ultimos(ultimos: dict):
    with (curado / "ids-ultimo.csv").open("w", encoding="utf-8", newline="") as h:
        w = csv.writer(h)
        w.writerow(["prefijo", "ultimo"])
        w.writerows(sorted(ultimos.items()))


def asignar_ids(filas):
    ruta = curado / "ids-lexico.csv"
    mapa = leer_mapa(ruta, "registro")
    ultimos = leer_ultimos()
    for i in mapa.values():
        ultimos[i[0]] = max(ultimos.get(i[0], 0), int(i[1:]))
    vivos = {}
    for f in filas:
        prefijo = "q" if f["lengua"] == "quechua" else "a"
        if f["registro"] not in mapa:
            ultimos[prefijo] = ultimos.get(prefijo, 0) + 1
            mapa[f["registro"]] = f"{prefijo}{ultimos[prefijo]:05d}"
        f["id"] = mapa[f["registro"]]
        vivos[f["registro"]] = f["id"]
    with ruta.open("w", encoding="utf-8", newline="") as h:
        w = csv.writer(h)
        w.writerow(["id", "registro"])
        w.writerows(sorted((i, r) for r, i in vivos.items()))
    escribir_ultimos(ultimos)


def construir_oraciones(crudas, clasificador):
    filas = []
    descartes = defaultdict(int)
    for f in crudas:
        f["variedad_quechua"] = ""
        f["variedad_aimara"] = "comun" if f["aimara"] else ""
        f["evidencia_quechua"] = ""
        if f["quechua"]:
            variedad, evidencia = clasificador.oracion_quechua(f["quechua"], f["declarada"])
            f["evidencia_quechua"] = evidencia
            if variedad:
                f["variedad_quechua"] = variedad
            else:
                descartes[(f["fuente_id"], evidencia.split(":")[0])] += 1
                f["registro"] = (f["fuente_id"], f["es"].lower(), f["quechua"].lower(), f["aimara"].lower())
                f["quechua"] = ""
        if f["es"] and (f["quechua"] or f["aimara"]):
            filas.append(f)
    vistos, unicas = set(), []
    for f in filas:
        k = (f["es"].lower(), f["quechua"].lower(), f["aimara"].lower())
        if k not in vistos:
            vistos.add(k)
            f["nivel"] = nivel_oracion(f["es"])
            f.setdefault("registro", (f["fuente_id"], *k))
            unicas.append(f)
    ruta = curado / "ids-oraciones.csv"
    mapa = leer_mapa(ruta, "registro")
    if not mapa and (curado / "oraciones.csv").exists():
        with (curado / "oraciones.csv").open(encoding="utf-8") as h:
            mapa = {"|".join((r["fuente_id"], r["es"].lower(), r["quechua"].lower(), r["aimara"].lower())): r["id"] for r in csv.DictReader(h)}
    ultimos = leer_ultimos()
    ultimos["o"] = max([ultimos.get("o", 0)] + [int(i[1:]) for i in mapa.values()])
    usados, vivos = set(), {}
    for f in unicas:
        llave = "|".join(f["registro"])
        if llave not in mapa or mapa[llave] in usados:
            ultimos["o"] += 1
            mapa[llave] = f"o{ultimos['o']:05d}"
        f["id"] = mapa[llave]
        usados.add(f["id"])
        vivos[llave] = f["id"]
    with ruta.open("w", encoding="utf-8", newline="") as h:
        w = csv.writer(h)
        w.writerow(["id", "registro"])
        w.writerows(sorted((i, r) for r, i in vivos.items()))
    escribir_ultimos(ultimos)
    unicas.sort(key=lambda f: f["id"])
    return unicas, dict(descartes)


def exportar_evaluacion():
    destino = datos / "evaluacion"
    destino.mkdir(parents=True, exist_ok=True)
    flores = crudo / "flores200" / "flores200_dataset" / "devtest"
    columnas = [(flores / f"{c}_Latn.devtest").read_text(encoding="utf-8").splitlines() for c in ("spa", "quy", "ayr")]
    filas = [{"id": f"e{i:04d}", "es": limpiar(e), "quechua": limpiar(q), "aimara": limpiar(a)}
             for i, (e, q, a) in enumerate(zip(*columnas), start=1)]
    escribir_csv(destino / "flores200-devtest-reservado.csv", filas, ["id", "es", "quechua", "aimara"])
    return len(filas)


def construir_conceptos(lexico):
    por_concepto = defaultdict(lambda: {"quechua": [], "aimara": []})
    for f in lexico:
        if f["concepto"]:
            por_concepto[f["concepto"]][f["lengua"]].append(f["id"])
    filas = []
    for concepto, d in sorted(por_concepto.items()):
        filas.append({
            "concepto": concepto,
            "quechua_ids": " ".join(d["quechua"]),
            "aimara_ids": " ".join(d["aimara"]),
            "trilingue": "si" if d["quechua"] and d["aimara"] else "no",
            "tema": tema_de(concepto),
        })
    return filas


def normal(texto: str) -> str:
    t = unicodedata.normalize("NFC", texto).lower().replace("’", "'").replace("´", "'")
    return re.sub(r"[^\w' ]", "", t).strip()


def escribir_csv(ruta: Path, filas, columnas):
    with ruta.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=columnas, extrasaction="ignore")
        w.writeheader()
        w.writerows(filas)


columnas_lexico = ["id", "lengua", "iso", "variante", "variedad", "variedad_evidencia", "forma", "glosa_es", "concepto", "categoria", "tema",
                   "nivel", "ipa", "ejemplo", "ejemplo_es", "fuente_id", "fuente_url", "licencia", "estado_revision", "confianza"]
columnas_oraciones = ["id", "es", "quechua", "aimara", "nivel", "fuente_id", "licencia", "alineacion", "variedad_quechua", "variedad_aimara"]


def escribir_sqlite(lexico, oraciones, conceptos, apoyo):
    ruta = curado / "tinku-contenido.sqlite"
    ruta.unlink(missing_ok=True)
    db = sqlite3.connect(ruta)
    db.executescript("""
        create table fuentes (id text primary key, nombre text, tipo text, lenguas text, url text,
            licencia text, redistribuible text, cita text, registros integer);
        create table lexico (id text primary key, lengua text, iso text, variante text, variedad text, variedad_evidencia text,
            forma text, glosa_es text, concepto text, categoria text, tema text, nivel text, ipa text,
            ejemplo text, ejemplo_es text, fuente_id text references fuentes(id), fuente_url text,
            licencia text, estado_revision text, confianza integer, audio text default '', audio_origen text default '',
            audio_credito text default '');
        create table oraciones (id text primary key, es text, quechua text, aimara text, nivel text,
            fuente_id text references fuentes(id), licencia text, alineacion text, variedad_quechua text, variedad_aimara text,
            audio_es text default '', audio_quechua text default '', audio_aimara text default '');
        create table conceptos (concepto text primary key, quechua_ids text, aimara_ids text,
            trilingue text, tema text);
        create table temas (id text primary key, nivel text, orden integer);
        create table apoyo (lengua text, forma text, termino text, fuente_id text);
        create virtual table lexico_fts using fts5(forma, glosa_es, content='lexico', content_rowid='rowid',
            tokenize='unicode61 remove_diacritics 2');
        create index lexico_lengua_tema on lexico(lengua, tema, nivel);
        create index oraciones_nivel on oraciones(nivel, fuente_id);
        create index apoyo_forma on apoyo(lengua, forma);
    """)
    conteo = defaultdict(int)
    for f in lexico:
        conteo[f["fuente_id"]] += 1
    for f in oraciones:
        conteo[f["fuente_id"]] += 1
    db.executemany("insert into fuentes values (?,?,?,?,?,?,?,?,?)",
                   [(f["id"], f["nombre"], f["tipo"], f["lenguas"], f["url"], f["licencia"],
                     f["redistribuible"], f["cita"], conteo[f["id"]]) for f in fuentes])
    db.executemany(f"insert into lexico ({','.join(columnas_lexico)}) values ({','.join('?' * len(columnas_lexico))})",
                   [tuple(f[c] for c in columnas_lexico) for f in lexico])
    db.executemany(f"insert into oraciones ({','.join(columnas_oraciones)}) values ({','.join('?' * len(columnas_oraciones))})",
                   [tuple(f[c] for c in columnas_oraciones) for f in oraciones])
    db.executemany("insert into conceptos values (?,?,?,?,?)",
                   [(c["concepto"], c["quechua_ids"], c["aimara_ids"], c["trilingue"], c["tema"]) for c in conceptos])
    db.executemany("insert into temas values (?,?,?)",
                   [(t, n, i) for i, (t, (n, _)) in enumerate(list(temas.items()) + [("general", ("B1", ""))])])
    db.executemany("insert into apoyo values (?,?,?,?)", apoyo)
    humanos = curado / "audio_humano.csv"
    if humanos.exists():
        with humanos.open(encoding="utf-8") as h:
            registros = {(r["lengua"], r["forma_norm"]): r for r in csv.DictReader(h)
                         if r["archivo"].startswith("humano/") and (curado / "audio" / r["archivo"]).exists()}
        db.executemany("update lexico set audio = ?, audio_origen = 'hablante', audio_credito = ? where id = ?",
                       [(f"/audio/{r['archivo']}", f"{r['hablante']} · {r['licencia']} · Lingua Libre / Wikimedia Commons", f["id"])
                        for f in lexico if (r := registros.get((f["lengua"], normal(f["forma"]))))])
    db.execute("update fuentes set registros = (select count(*) from lexico where audio_origen = 'hablante') where id = 'lingua_libre'")
    db.execute("update fuentes set registros = (select count(*) from lexico where variedad_evidencia like '%crossandean%') where id = 'crossandean'")
    db.execute("insert into lexico_fts(lexico_fts) values ('rebuild')")
    db.commit()
    db.close()
    return ruta


if __name__ == "__main__":
    curado.mkdir(parents=True, exist_ok=True)
    crudas = leer_oraciones()
    clasificador = preparar_clasificador(crudas)
    lexico, apoyo = construir_lexico(clasificador)
    oraciones, descartes = construir_oraciones(crudas, clasificador)
    conceptos = construir_conceptos(lexico)
    escribir_csv(curado / "fuentes.csv", fuentes, list(fuentes[0].keys()))
    escribir_csv(curado / "lexico.csv", lexico, columnas_lexico)
    escribir_csv(curado / "oraciones.csv", oraciones, columnas_oraciones)
    escribir_csv(curado / "conceptos.csv", conceptos, ["concepto", "quechua_ids", "aimara_ids", "trilingue", "tema"])
    reservadas = exportar_evaluacion()
    ruta = escribir_sqlite(lexico, oraciones, conceptos, apoyo)
    tri = sum(1 for c in conceptos if c["trilingue"] == "si")
    por_variedad = defaultdict(int)
    for f in lexico:
        por_variedad[(f["lengua"], f["variedad"], f["fuente_id"])] += 1
    print(f"lexico: {len(lexico)}")
    for k, v in sorted(por_variedad.items()):
        print(f"  {k}: {v}")
    print(f"oraciones: {len(oraciones)}; quechua descartado por variedad: {descartes}")
    print(f"conceptos: {len(conceptos)} trilingues: {tri}")
    print(f"evaluación reservada (FLORES devtest): {reservadas}")
    print(f"sqlite: {ruta}")
