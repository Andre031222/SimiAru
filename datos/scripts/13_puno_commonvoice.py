import csv
import re
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path

datos = Path(__file__).resolve().parents[1]
crudo = datos / "fuentes" / "crudo" / "commonvoice-qxp"
curado = datos / "curado"
base = "https://raw.githubusercontent.com/QuechuaBase/asr-puno-quechua/main/data/splits_cv26"
particiones = ("train", "dev", "test")


def descargar():
    for tipo, carpeta in (("scripted", crudo), ("spontaneous", crudo / "espontaneo")):
        carpeta.mkdir(parents=True, exist_ok=True)
        for p in particiones:
            destino = carpeta / f"{p}.tsv"
            if not destino.exists():
                urllib.request.urlretrieve(f"{base}/{tipo}/{p}.tsv", destino)


def tokens(texto: str) -> list[str]:
    return re.findall(r"[a-zñáéíóúäëïöü']+", texto.lower().replace("’", "'").replace("´", "'"))


def leer(carpeta: Path):
    for p in particiones:
        with (carpeta / f"{p}.tsv").open(encoding="utf-8") as h:
            yield from csv.DictReader(h, delimiter="\t")


if __name__ == "__main__":
    descargar()
    frases = {r["sentence_id"]: r["sentence"].strip() for r in leer(crudo) if r["sentence"].strip()}
    espontaneo = [r["transcription"].strip() for r in leer(crudo / "espontaneo") if r.get("type") == "gold" and r["transcription"].strip()]

    frecuencia, en_frases = Counter(), defaultdict(int)
    for texto in frases.values():
        for t in set(tokens(texto)):
            en_frases[t] += 1
        frecuencia.update(tokens(texto))
    for texto in espontaneo:
        frecuencia.update(tokens(texto))

    with (curado / "puno_formas.csv").open("w", encoding="utf-8", newline="") as h:
        w = csv.writer(h)
        w.writerow(["forma", "frecuencia", "frases"])
        for forma, n in sorted(frecuencia.items(), key=lambda x: (-x[1], x[0])):
            w.writerow([forma, n, en_frases.get(forma, 0)])
    with (curado / "puno_frases.csv").open("w", encoding="utf-8", newline="") as h:
        w = csv.writer(h)
        w.writerow(["id", "texto"])
        for i, texto in sorted(frases.items(), key=lambda x: x[1]):
            w.writerow([f"cvqxp-{i[:12]}", texto])
    print(f"frases leídas: {len(frases)} · transcripciones espontáneas gold: {len(espontaneo)} · formas distintas: {len(frecuencia)}")
