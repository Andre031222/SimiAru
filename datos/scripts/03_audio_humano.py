import csv
import hashlib
import html
import json
import re
import sqlite3
import subprocess
import tempfile
import time
import urllib.parse
import unicodedata
import urllib.request
from pathlib import Path

datos = Path(__file__).resolve().parents[1]
commons = datos / "fuentes" / "crudo" / "wikimedia-commons-audio"
curado = datos / "curado"
destino = curado / "audio" / "humano"

variedad_de_codigo = {"qxp": "quechua de Puno", "que": "quechua de Puno", "quy": "quechua ayacuchano", "quz": "quechua cuzqueño", "quh": "quechua boliviano", "aimara": "aimara"}
lengua_de_codigo = {"qxp": "quechua", "que": "quechua", "quy": "quechua", "quz": "quechua", "quh": "quechua"}
patron_ll = re.compile(r"^File:LL-Q\d+ \((\w+)\)-([^-]+)-(.+)\.\w+$")
patron_ay = re.compile(r"^File:(?:Ay|Aymara)-([^-.]+)(?:-.+)?\.\w+$")


def normal(texto: str) -> str:
    t = unicodedata.normalize("NFC", texto).lower().replace("’", "'").replace("´", "'").replace("ʼ", "'")
    return re.sub(r"[^\w' ]", "", t).strip()


def hablante(artista: str, respaldo: str) -> str:
    texto = re.sub(r"<[^>]+>", " ", html.unescape(artista or ""))
    encontrado = re.search(r"Speaker:\s*([^\n]+?)\s{2,}|Speaker:\s*(.+)$", texto)
    nombre = (encontrado.group(1) or encontrado.group(2)).strip() if encontrado else texto.strip()
    return re.sub(r"\s+", " ", nombre)[:60] or respaldo


def grabaciones():
    for manifiesto in sorted(commons.glob("manifest*.json")):
        for r in json.loads(manifiesto.read_text(encoding="utf-8")):
            if not r["mime"].startswith(("audio/", "application/ogg")):
                continue
            titulo = r["title"]
            if m := patron_ll.match(titulo):
                codigo, locutor, palabra = m.groups()
                lengua = lengua_de_codigo.get(codigo)
            elif m := patron_ay.match(titulo):
                palabra, locutor, lengua, codigo = m.group(1), "", "aimara", "aimara"
                if palabra.lower() == "fonema":
                    continue
            else:
                continue
            if lengua:
                yield lengua, palabra, f"{hablante(r.get('artist', ''), locutor)} ({variedad_de_codigo.get(codigo, codigo)})", r["license"], r["url"].split("?")[0]


def locales():
    indice = {}
    for archivo in commons.glob("audio_*/*"):
        nombre = urllib.parse.unquote(archivo.name.split("?")[0])
        indice[nombre] = archivo
    return indice


def descargar(url: str) -> bytes:
    peticion = urllib.request.Request(url, headers={"User-Agent": "TINKU-Aprende/1.0 (academic research; Universidad Nacional del Altiplano, Puno)"})
    for intento in range(2):
        try:
            datos_audio = urllib.request.urlopen(peticion, timeout=60).read()
            time.sleep(2.0)
            return datos_audio
        except urllib.error.HTTPError as e:
            if e.code != 429:
                raise
            time.sleep(20)
    raise RuntimeError("límite de solicitudes")


def convertir(tarea, indice):
    lengua, palabra, locutor, licencia, url, relativo = tarea
    salida = curado / "audio" / relativo
    if salida.exists():
        return tarea
    salida.parent.mkdir(parents=True, exist_ok=True)
    nombre = urllib.parse.unquote(url.rsplit("/", 1)[-1])
    local = indice.get(nombre)
    with tempfile.NamedTemporaryFile(suffix=Path(nombre).suffix) as tmp:
        tmp.write(local.read_bytes() if local else descargar(url))
        tmp.flush()
        subprocess.run(
            ["ffmpeg", "-loglevel", "error", "-y", "-i", tmp.name, "-af",
             "silenceremove=start_periods=1:start_threshold=-45dB,areverse,silenceremove=start_periods=1:start_threshold=-45dB,areverse",
             "-ac", "1", "-codec:a", "libmp3lame", "-b:a", "64k", str(salida)],
            check=True,
        )
    return tarea


def escribir(listas):
    with (curado / "audio_humano.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["lengua", "forma_norm", "palabra", "hablante", "licencia", "url", "archivo"])
        for lengua, palabra, locutor, licencia, url, relativo in listas:
            w.writerow([lengua, normal(palabra), palabra, locutor, licencia, url, relativo])


def seguro(tarea, indice):
    try:
        return convertir(tarea, indice)
    except Exception as e:
        print(f"fallo {tarea[4]}: {e}", flush=True)
        return None


if __name__ == "__main__":
    db = sqlite3.connect(curado / "tinku-contenido.sqlite")
    formas = {(l, normal(f)) for l, f in db.execute("select lengua, forma from lexico")}
    tareas, vistos = [], set()
    for lengua, palabra, locutor, licencia, url in grabaciones():
        clave = (lengua, normal(palabra))
        if clave in formas and clave not in vistos:
            vistos.add(clave)
            relativo = f"humano/{lengua}/{hashlib.sha1(url.encode()).hexdigest()[:16]}.mp3"
            tareas.append((lengua, palabra, locutor, licencia, url, relativo))
    print(f"grabaciones que coinciden con el léxico: {len(tareas)}", flush=True)
    indice = locales()
    tareas.sort(key=lambda t: urllib.parse.unquote(t[4].rsplit("/", 1)[-1]) not in indice)
    print(f"disponibles en disco: {sum(1 for t in tareas if urllib.parse.unquote(t[4].rsplit('/', 1)[-1]) in indice)}", flush=True)
    listas = []
    pendientes = tareas
    for pasada in range(1, 4):
        fallidas = []
        for i, tarea in enumerate(pendientes, start=1):
            if t := seguro(tarea, indice):
                listas.append(t)
            else:
                fallidas.append(tarea)
            if i % 100 == 0:
                print(f"pasada {pasada}: {i}/{len(pendientes)}", flush=True)
                escribir(listas)
        escribir(listas)
        print(f"pasada {pasada} terminada: {len(fallidas)} pendientes", flush=True)
        if not fallidas:
            break
        pendientes = fallidas
        time.sleep(120)
    print(f"audio humano disponible: {len(listas)}")
