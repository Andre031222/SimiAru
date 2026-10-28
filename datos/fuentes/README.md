# Registro de fuentes

Una fuente se registra antes de integrarla, con estos datos: URL estable, lenguas y variedad, tipo de recurso, licencia, fecha de acceso, condiciones de redistribución y uso previsto. Los originales se guardan sin modificar en `crudo/`, carpeta que no se redistribuye. La clave de cita es la de `04-paper/manuscrito/referencias.bib`. Las claves `key2023ids` y `blum2023quechua` son nuevas y deben añadirse al .bib.

Desde el 25-10-2026 solo se aceptan fuentes con licencia CC0, CC BY o CC BY-SA, de dominio público o con textos legales oficiales. Las fuentes con licencia no comercial o no declarada se retiraron (ver abajo).

## Fuentes integradas

| Identificador | Recurso | Lenguas | Licencia (verificada) | Acceso | Confianza | Uso en eLOP | Cita |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `wikcionario_es` | Wikcionario en español, extracción wiktextract de Kaikki.org (https://kaikki.org/eswiktionary/) | quz, quy, quh, qu, ay, es | CC BY-SA 4.0 | 29-09-2026 | 3 | léxico, IPA, ejemplos y traducciones | `ylonen2022wiktextract` |
| `wikcionario_en` | Wiktionary en inglés, extracción wiktextract de Kaikki.org (https://kaikki.org/dictionary/English/). Solo se usan tablas de traducción con español y quechua o aimara en la misma acepción | qu, ay, es | CC BY-SA 4.0 | 25-10-2026 | 2 | léxico | `ylonen2022wiktextract` |
| `wikidata_lexemas` | Lexemas de Wikidata: Q5218 quechua y Q4627 aimara (https://www.wikidata.org/wiki/Wikidata:Lexicographical_data) | qu, ay, es | CC0 1.0 | 29-09-2026 | 2 | léxico | `vrandecic2014wikidata` |
| `ids` | Intercontinental Dictionary Series, lista aimara de Félix Layme Pairumani (https://ids.clld.org/contributions/269), versión CLDF de Lexibank (https://github.com/lexibank/ids). Las glosas en español vienen de la lista Key-2016-1310 de Concepticon (CC BY 4.0) | ayr, es | CC BY 4.0 (ids.clld.org y metadata.json) | 25-10-2026 | 3 | léxico aimara. La notación fonémica se transcribe al alfabeto aimara oficial en `02_construir_base.py` | `key2023ids` |
| `crossandean` | Blum, Barrientos, Ingunza y Poirier (2023), clasificación filolingüística del quechua, CLDF (https://github.com/lexibank/crossandean). Las glosas en español vienen de Heggarty-2005-150 de Concepticon | quechua de 40 localidades, aimara de Huancané y Sullkatiti | CC BY 4.0 (README y metadata.json) | 25-10-2026 | — | solo evidencia de variedad, no se muestran sus formas (ver `../VARIEDADES.md`) | `blum2023quechua` |
| `commonvoice_qxp` | Common Voice, quechua de Puno: frases leídas curadas por un hablante y habla espontánea (solo transcripciones *gold*), con las particiones de QuechuaBase (https://github.com/QuechuaBase/asr-puno-quechua) | qxp | CC0 1.0 | 05-10-2026 | — | evidencia de variedad Qullaw, marca `en_puno` y frases de ejemplo sin traducir | `ardila2020commonvoice` |
| `americasnli` | AmericasNLI, conjunto dev (https://github.com/abteen/americasnli) | es, quy, aym | CC BY-SA 4.0 | 29-09-2026 | — | lecturas trilingües y evidencia Chanka | `ebrahimi2022americasnli` |
| `flores200` | FLORES-200, conjunto dev (https://github.com/facebookresearch/flores) | spa, quy, ayr | CC BY-SA 4.0 | 29-09-2026 | — | lecturas trilingües y evidencia Chanka | `nllb2022` |
| `tatoeba` | Tatoeba, oraciones que/aym enlazadas al español (https://tatoeba.org/) | que, aym, es | CC BY 2.0 FR | 29-09-2026 | — | lecturas. El quechua solo se conserva si tiene rasgos del Collao | `tatoeba` |
| `globalvoices_opus` | Global Voices español–aimara (OPUS), distribuido en AmericasNLP 2021 | es, aym | CC BY 3.0 | 29-09-2026 | — | lecturas avanzadas, alineación automática | `tiedemann2012opus` |
| `dudh` | Declaración Universal de Derechos Humanos (quz, quy, quh, aym), recopilada en AmericasNLP 2024 | es, quz, quy, quh, aym | libre reproducción (ONU) | 29-09-2026 | — | lecturas formales | `degibert2023four` |
| `constituciones` | Constituciones del Perú y de Bolivia en quechua y aimara, recopiladas en AmericasNLP 2024 | es, que, quh, aym | texto legal oficial (D. Leg. 822, art. 9) | 29-09-2026 | — | lecturas formales | `degibert2023four` |
| `lingua_libre` | Grabaciones de Lingua Libre y Wikimedia Commons | qxp, quz, quy, quh, ay | CC BY-SA 4.0, CC BY 4.0 o CC0, según el archivo | 29-09-2026 | — | audio de hablantes con crédito | `lingualibre` |

La confianza ordena la selección de ejercicios: 3 para un diccionario o una lista de autor, 2 para Wikidata y las traducciones del Wiktionary en inglés.

No hay voz sintética. `lexico.audio` solo enlaza grabaciones de hablantes (`audio_origen = 'hablante'`). Las oraciones no tienen audio, y la web lee el español con la voz del navegador.

## Fuentes retiradas el 25-10-2026

| Fuente | Motivo | Qué se eliminó |
| --- | --- | --- |
| PanLex | licencia no comercial (CC BY-NC-SA 4.0) | unas 50 000 entradas léxicas, el crudo `crudo/panlex/` y su descarga |
| Diccionario MINEDU de quechua ayacuchano y Dict_misc (AmericasNLP 2021) | licencia no declarada | 4 392 entradas, 4 109 oraciones de ejemplo y los archivos `dict.*`. Las oraciones dev de AmericasNLI se mantienen |
| MMS-TTS (Meta) | licencia no comercial (CC BY-NC 4.0) | voz sintética de palabras y oraciones (`audio/ayr`, `quy`, `quz`, `spa`, `v2-*`) y los scripts 04 y 11 |
| Gemini TTS | términos de servicio, no es licencia abierta | `audio/gemini-kore-quechua` y el script 04c |
| Voz Paulina de macOS | licencia del sistema operativo | `audio/mac-paulina` y los scripts 04b y 09 |

## Fuentes evaluadas y no integradas

| Carpeta en `crudo/` o recurso | Licencia | Motivo |
| --- | --- | --- |
| `opus` (wikimedia es–qu, ay–es) | CC BY-SA 4.0 | texto enciclopédico con variedades mezcladas (incluye quechua central, p. ej. *tsay*) y pocas líneas de aimara (154). Poco útil para principiantes |
| `opus` (NLLB ay–es, QED) | varía | ruidoso, religioso o solo para investigación |
| `kaikki-enwiktionary-quechua` | CC BY-SA 4.0 | 2 858 entradas con glosa solo en inglés y casi sin marcas de variedad. Se usan en su lugar las tablas de traducción con español |
| Wikidata, etiquetas de ítems (`wikidata/labels_items_*.csv`) | CC0 | sobre todo nombres propios y etiquetas copiadas del español |
| `bertonio-1612-archive-org` | dominio público | grafía colonial. Modernizarla requiere un experto |
| `siminchik-iwslt2023` | ND | habla de radio, útil para reconocimiento de voz y no para lecciones |
| `aymara-spanish-parallel-corpus-hf` | derechos de terceros | raspado de Bible.com. No lo lee ningún script |
| `nllb-md` | CC BY-NC 4.0 | par inglés–aimara no comercial. No lo lee ningún script |
| Wiktionary en inglés, aimara | — | Kaikki no publica una extracción por lengua para el aimara. Solo se usan las tablas de traducción |

## Datos reservados para evaluación

| Recurso | Archivo | Registros | Regla |
| --- | --- | --- | --- |
| FLORES-200 devtest (spa, quy, ayr) | `datos/evaluacion/flores200-devtest-reservado.csv` | 1 012 | nunca se usa en lecciones, ejercicios ni recuperación |

## Procedimiento

```bash
python3 datos/scripts/01_descargar_fuentes.py
python3 datos/scripts/13_puno_commonvoice.py
python3 datos/scripts/02_construir_base.py
python3 datos/scripts/03_audio_humano.py
python3 datos/scripts/02_construir_base.py
python3 datos/scripts/10_calidad_glosas.py
python3 datos/scripts/08_ejemplos_gramatica.py
uv run datos/scripts/07_cargar_postgres.py
```

`01_descargar_fuentes.py traducciones` descarga solo el extracto del Wiktionary en inglés: recorre en flujo el volcado de 534 MB y guarda unas 2 000 entradas. `03_audio_humano.py` necesita una base ya construida para saber qué formas buscar, y por eso `02_construir_base.py` se ejecuta dos veces. `05_exportar_cifras.py` escribe las cifras del artículo en la carpeta del paper, fuera de este repositorio.


## Corpus de atestiguación

| Recurso | Licencia | Uso |
| --- | --- | --- |
| Wikipedia en quechua y en aimara (volcados `quwiki` y `aywiki`, descargados el 28-10-2026 en `crudo/wikipedia/`) | CC BY-SA 4.0 | solo se cuentan apariciones de formas para el núcleo; no se publica texto |
| `wordfreq` (frecuencia del español) | datos CC BY-SA 4.0, código Apache 2.0 | solo para filtrar glosas raras |
