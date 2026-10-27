<p align="center">
  <img src="figuras/logo-elop.webp" width="260" alt="eLOP">
</p>

<h1 align="center">SimiAru</h1>

<p align="center"><b>Open, variety-aware Spanish–Quechua–Aymara resource for language learners</b><br>
<i>simi</i> and <i>aru</i> mean “word” in Quechua and Aymara</p>

<p align="center">
  <a href="LICENSE-DATA"><img src="https://img.shields.io/badge/Data-CC%20BY--SA%204.0-2E7D32?style=flat-square" alt="Data licence"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/Code-MIT-337AB7?style=flat-square" alt="Code licence"></a>
  <a href="https://elop.ginit.dev"><img src="https://img.shields.io/badge/Platform-elop.ginit.dev-5D2DFD?style=flat-square" alt="eLOP platform"></a>
  <img src="https://img.shields.io/badge/Entries-6%2C861-0F2444?style=flat-square" alt="Entries">
  <img src="https://img.shields.io/badge/Sentences-10%2C853-0F2444?style=flat-square" alt="Sentences">
  <img src="https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python">
</p>

<p align="center"><a href="README_ES.md">Leer en español</a></p>

---

## Overview

SimiAru is the lexical and sentence resource behind [eLOP](https://elop.ginit.dev), a web platform that teaches Southern Quechua and Aymara to Spanish speakers in Puno, Peru. It solves two problems of earlier resources:

1. **Mixed varieties.** Every entry is labelled Collao, Chanka, northern Aymara, southern Aymara or shared, by deterministic rules with recorded evidence.
2. **Restrictive licences.** Only CC0, CC BY, CC BY-SA, public-domain and official sources are used. Everything can be redistributed and used commercially with attribution.

<p align="center">
  <img src="figuras/fig4.png" width="92%" alt="Pipeline">
  <br><sub><b>Figure 1.</b> Licence audit → variety classification → variety-tagged resource → platform filter that keeps each learner within one variety.</sub>
</p>

## Varieties

| Language | Variety | Area | Entries |
|---|---|---|---:|
| Quechua | Collao (Qullaw) | Puno, Cusco, Arequipa, Moquegua, part of Apurímac, Bolivia | 2,663 |
| Quechua | Chanka | Ayacucho, Huancavelica, part of Apurímac | 116 |
| Quechua | shared | attested in both, or without variety features | 2,504 |
| Aymara | northern | Huancané, Moho, San Antonio de Putina, part of Azángaro | 5 |
| Aymara | southern | Chucuito, El Collao, Yunguyo, Puno; Moquegua, Tacna, Bolivian altiplano | 19 |
| Aymara | shared | no regional attestation in open sources | 1,554 |

Rules (full detail in [`datos/VARIEDADES.md`](datos/VARIEDADES.md)):

1. Ejective (`p' t' ch' k' q'`), aspirated (`ph th chh kh qh`) or progressive *-sha-* → **Collao**, whatever the source says.
2. Attested in Collao and Chanka evidence → **shared**.
3. Attested in one variety → **that variety**.
4. No evidence → **shared**, flagged as neutral.

Aymara is northern or southern only when the Huancané and Sullkatiti lists of [CrossAndean](https://doi.org/10.5281/zenodo.19184362) give different forms for the same concept.

## Key results

<table>
<tr><td valign="top" width="50%">

**Licence audit** (earlier corpus → SimiAru)

| | Before | After |
|---|---:|---:|
| Lexical entries | 58,265 | 6,861 |
| from non-commercial or unlicensed sources | 54,667 (93.8%) | 0 |
| Sentences | 15,583 | 10,853 |
| Entries with audio | 57,492 | 1,011 |
| synthetic audio | 55,535 (96.6%) | 0 |

</td><td valign="top" width="50%">

**Variety control**

| Check | Result |
|---|---:|
| Chanka entries with Collao features, before | 156 |
| Chanka entries with Collao features, after | 0 |
| Exercises generated (4 learner profiles) | 12,025 |
| Targets or distractors outside the learner's variety | 0 |
| Swadesh 100 coverage, Collao learners | 63% → 93% |
| Swadesh 100 coverage, Chanka learners | 95% → 85% |

</td></tr>
</table>

<p align="center">
  <img src="figuras/fig1.png" width="92%" alt="Licence audit">
  <br><sub><b>Figure 2.</b> Composition by source and licence class before and after the audit.</sub>
</p>

<p align="center">
  <img src="figuras/fig3.png" width="92%" alt="Coverage">
  <br><sub><b>Figure 3.</b> Basic-vocabulary coverage per learner variety (Swadesh 100 and Leipzig–Jakarta), with Wilson 95% intervals.</sub>
</p>

<p align="center">
  <img src="figuras/fig5.png" width="70%" alt="eLOP platform">
  <br><sub><b>Figure 4.</b> eLOP: an exercise drawn from the learner's variety (a) and a dictionary entry with variety, source and licence (b).</sub>
</p>

## Repository structure

```
SimiAru/
├── datos/
│   ├── curado/              # the resource (CSV, UTF-8)
│   │   ├── lexico.csv       # 6,861 entries with variety, evidence, gloss, source and licence
│   │   ├── oraciones.csv    # 10,853 sentences aligned with Spanish
│   │   ├── conceptos.csv    # Quechua–Aymara links through Spanish
│   │   ├── audio_humano.csv # speaker recordings: speaker, licence and URL
│   │   ├── puno_formas.csv  # forms attested in Common Voice Puno Quechua
│   │   └── ...
│   ├── fuentes/README.md    # source registry with licences
│   ├── scripts/             # download, build and variety classifier
│   ├── evaluacion/          # FLORES-200 devtest, held out
│   ├── VARIEDADES.md        # classification rules
│   └── INVENTARIO.md        # counts
├── experimentos/lre/        # evaluation: scripts, results (CSV), figures, review kit
└── figuras/                 # figures used in this README
```

## Data format

`datos/curado/lexico.csv`

| Column | Meaning |
|---|---|
| `id` | stable identifier, kept across rebuilds |
| `lengua` | `quechua` or `aimara` |
| `iso` | language code given by the source |
| `variedad` | `qullaw`, `chanka`, `norte`, `sur` or `comun` |
| `variedad_evidencia` | rule or evidence that decided the variety |
| `forma`, `glosa_es` | form and Spanish gloss |
| `tema`, `nivel` | beginner topic and level (A1–B2) |
| `fuente_id`, `fuente_url`, `licencia` | provenance and licence of the entry |
| `confianza` | source confidence (3 curated, 2 bridged or Wikidata, 1 aggregated) |

`datos/curado/oraciones.csv` has `es`, `quechua`, `aimara`, `fuente_id`, `licencia`, `variedad_quechua` and `variedad_aimara`.

## Rebuild

Requires Python 3.12 and [uv](https://docs.astral.sh/uv/).

```bash
python3 datos/scripts/01_descargar_fuentes.py
python3 datos/scripts/03_audio_humano.py
python3 datos/scripts/02_construir_base.py
python3 datos/scripts/10_calidad_glosas.py
python3 datos/scripts/08_ejemplos_gramatica.py
```

The build is deterministic: the same sources give the same resource and the same identifiers. The evaluation is described in [`experimentos/lre/README.md`](experimentos/lre/README.md).

## Licence and attribution

- **Data** (`datos/curado/`): [CC BY-SA 4.0](LICENSE-DATA). Several sources are CC BY-SA, so derived data must keep this licence.
- **Code** (`datos/scripts/`, `experimentos/lre/scripts/`): [MIT](LICENSE).
- Credit the original sources: Wiktionary (CC BY-SA 4.0), Wikidata (CC0), Intercontinental Dictionary Series (CC BY 4.0), CrossAndean (CC BY 4.0), AmericasNLI and FLORES-200 (CC BY-SA 4.0), Global Voices (CC BY 3.0), Tatoeba (CC BY 2.0 FR), Common Voice (CC0), Lingua Libre (per recording). Full registry in [`datos/fuentes/README.md`](datos/fuentes/README.md).
- Audio files are not stored here; `audio_humano.csv` links each recording to Wikimedia Commons with its speaker and licence.

## Limitations

- *Chanka* means attested in Chanka, not exclusive to it.
- 91% of Aymara entries have no regional evidence in open sources.
- Greetings with Spanish glosses are almost absent from open sources.
- Glosses have not yet been validated by speakers; the review kit is in `experimentos/lre/revision/`.

## Citation

A journal article describing this resource is in preparation. Until then, cite the repository (see [`CITATION.cff`](CITATION.cff)):

```bibtex
@misc{vilcasolorzano2026simiaru,
  title  = {SimiAru: open, variety-aware Spanish--Quechua--Aymara resource of the eLOP platform},
  author = {Vilca-Solorzano, Richar Andre and Torres-Cruz, Fred and Yana-Yucra, Dina Maribel and Quispe-Vargas, Renato and Ib{\'a}{\~n}ez-Quispe, Vladimiro},
  year   = {2026},
  url    = {https://github.com/Andre031222/SimiAru}
}
```

## Contact

Richar Andre Vilca Solorzano · [ORCID 0009-0003-2385-5263](https://orcid.org/0009-0003-2385-5263) · ravilcasolorzano@gmail.com
