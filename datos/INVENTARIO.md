# Inventario de datos — eLOP

Corte del 25 de octubre de 2026. Las cifras salen de `curado/tinku-contenido.sqlite` y del esquema `contenido` de PostgreSQL, cargado por `scripts/07_cargar_postgres.py`. El corpus se reconstruyó solo con fuentes abiertas, es decir, sin PanLex, sin el diccionario MINEDU y sin voz sintética. Cada entrada lleva una variedad asignada por las reglas de `VARIEDADES.md`. Licencias y procedencia en `fuentes/README.md`.

## Resumen

| Recurso | Cantidad |
| --- | --- |
| Entradas léxicas | 6 861 (5 283 quechua, 1 578 aimara) |
| Entradas aptas para ejercicios | 6 243 |
| Oraciones paralelas con español | 10 853 (5 119 con quechua, 9 580 con aimara) |
| Oraciones trilingües (español–quechua–aimara) | 3 846 |
| Conceptos enlazados por el español | 3 904 (827 trilingües) |
| Entradas con voz de hablante real | 1 011 (Lingua Libre / Wikimedia Commons, 928 MP3, 8,3 MB) |
| Voz sintética | ninguna |
| Ejemplos de gramática atestiguados | 1 069 en 15 unidades |
| Oraciones reservadas para evaluación | 1 012 (FLORES-200 devtest) |
| Fuentes registradas en `contenido.fuentes` | 13, con `commonvoice_qxp` |

## Léxico por variedad y fuente

| Lengua | Variedad | Wikcionario es | Wiktionary en | Wikidata | IDS | Total | Aptas |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Quechua | `qullaw` | 1 223 | 644 | 796 | — | 2 663 | 2 335 |
| Quechua | `comun` | 326 | 1 249 | 929 | — | 2 504 | 2 306 |
| Quechua | `chanka` | 8 | 65 | 43 | — | 116 | 108 |
| Aimara | `comun` | 620 | 120 | 5 | 809 | 1 554 | 1 471 |
| Aimara | `sur` | 12 | 1 | — | 6 | 19 | 18 |
| Aimara | `norte` | 2 | 1 | — | 2 | 5 | 5 |
| **Total** | | **2 191** | **2 080** | **1 773** | **817** | **6 861** | **6 243** |

Evidencia del quechua `comun`: 736 entradas atestiguadas en ambas variedades (`ambas:`) y 1 768 sin rasgos propios de ninguna (`neutra`). Del quechua `qullaw`, 1 510 tienen eyectivas o aspiradas. *crossandean* aporta evidencia a 271 entradas, y 780 entradas tienen forma atestiguada en Common Voice de Puno (`en_puno`).

## Cobertura por tema (entradas aptas)

| Tema | Quechua | Aimara |
| --- | ---: | ---: |
| saludos | 4 | 2 |
| números | 30 | 23 |
| familia | 40 | 33 |
| cuerpo | 59 | 43 |
| colores | 20 | 13 |
| animales | 72 | 60 |
| comida | 36 | 26 |
| naturaleza | 67 | 53 |
| hogar | 23 | 17 |
| vestido | 21 | 17 |
| tiempo | 27 | 28 |
| comunidad | 16 | 11 |
| personas | 33 | 18 |
| acciones | 138 | 55 |
| cualidades | 61 | 37 |
| emociones | 17 | 12 |
| general | 4 085 | 1 046 |

Los saludos son el punto débil. Las fuentes abiertas apenas registran fórmulas de saludo con glosa española, y no se añaden saludos sin fuente.

## Oraciones por fuente

| Fuente | Total | Con quechua | Con aimara | Trilingües | Variedad del quechua | Licencia |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| Global Voices (OPUS) | 5 085 | — | 5 085 | — | — | CC BY 3.0 |
| Constituciones del Perú y de Bolivia | 3 507 | 2 960 | 2 406 | 1 859 | qullaw | texto legal oficial |
| FLORES-200 dev | 997 | 922 | 997 | 922 | chanka | CC BY-SA 4.0 |
| AmericasNLI | 994 | 985 | 994 | 985 | chanka | CC BY-SA 4.0 |
| Declaración Universal de Derechos Humanos | 171 | 160 | 91 | 80 | 55 chanka, 105 qullaw | libre reproducción (ONU) |
| Tatoeba | 99 | 92 | 7 | — | qullaw | CC BY 2.0 FR |
| **Total** | **10 853** | **5 119** | **9 580** | **3 846** | | |

Se quitó el lado quechua de las oraciones que mezclan variedades o cuya variedad no consta: 109 oraciones de fuentes chanka con rasgos del Collao (AmericasNLI 9, FLORES 75, DUDH quy 25), 411 de la Constitución del Perú sin rasgos del Collao y 307 de Tatoeba, que incluyen kichwa ecuatoriano. Todo el aimara de las oraciones es `comun`.

## Identificadores estables

`curado/ids-lexico.csv` fija el identificador de cada entrada viva (lengua, forma, glosa y fuente). `curado/ids-oraciones.csv` hace lo mismo con las oraciones y se sembró con los identificadores anteriores. `curado/ids-ultimo.csv` guarda el último número usado de cada prefijo, para que los identificadores de entradas retiradas nunca se reutilicen. Tras la reconstrucción, 3 586 entradas léxicas y 10 759 oraciones conservan su identificador anterior, y ninguno se reasignó a otra palabra. Las tarjetas de usuarios que apuntaban a entradas retiradas (PanLex y MINEDU) quedan huérfanas.

## Gramática

`fuentes/gramatica.json` contiene 15 unidades: 9 de quechua y 6 de aimara. `scripts/08_ejemplos_gramatica.py` reúne 1 069 ejemplos atestiguados en las oraciones, entre 8 y 263 por unidad. Antes eran 3 522; la caída se debe a que el diccionario de raíces es más pequeño y a que ya no están las oraciones de MINEDU. Las unidades de posesivos quedan con pocos ejemplos: 9 en quechua y 8 en aimara.

## Calidad de glosas

`scripts/10_calidad_glosas.py` calcula el soporte de cada glosa con las fuentes que coinciden en forma y sentido (tabla `apoyo` de la base SQLite), recorta las glosas largas a sus primeras acepciones, marca las entradas aptas y las principales, y calcula `desplazada` entre `chanka` y `qullaw`. El informe está en `curado/calidad-glosas.json`. `fuentes/revision-glosas.csv` conserva las 271 revisiones pendientes que siguen vigentes. `fuentes/correcciones-glosas.csv` quedó vacío porque sus 11 correcciones se referían a glosas de PanLex.

## Datos originales descargados (`fuentes/crudo/`)

| Colección | Tamaño | Estado |
| --- | ---: | --- |
| Siminchik (habla quechua, IWSLT 2023) | 414 MB | no integrada |
| Imágenes de palabras (Commons) | 208 MB | fotos de la web |
| Audio de Wikimedia Commons y Lingua Libre | 120 MB | integrada |
| Wikcionario en español (Kaikki) | 97 MB | integrada |
| Wikidata | 68 MB | lexemas integrados |
| Corpus aimara–español de Hugging Face | 40 MB | descartada; no se lee |
| IDS (Lexibank) | 38 MB | aimara integrado |
| Wiktionary en inglés, quechua (Kaikki) | 30 MB | no integrada (solo glosas en inglés) |
| FLORES-200 | 25 MB | dev integrado; devtest reservado |
| OPUS | 16 MB | evaluada y no integrada |
| AmericasNLP 2024 | 11 MB | DUDH y constituciones |
| Common Voice qxp (transcripciones) | 11 MB | evidencia Qullaw y frases de Puno |
| Tatoeba | 6 MB | integrada |
| NLLB-MD | 5 MB | descartada; no se lee |
| Bertonio 1612 | 3 MB | no integrada |
| Wiktionary en inglés, tablas de traducción | 2 MB | integrada |
| AmericasNLP 2021 (sin `dict.*`) | 2 MB | AmericasNLI y Global Voices |
| *crossandean* (Lexibank) | 1 MB | evidencia de variedad |

## Verificación del 25-10-2026 (PostgreSQL)

- 0 entradas con `fuente_id` panlex o minedu_americasnlp y 0 filas de esas fuentes en `contenido.fuentes` y `contenido.oraciones`.
- 0 entradas `chanka` con eyectivas o aspiradas, y 0 oraciones `chanka` con eyectivas.
- 0 audios que no sean de hablante o que apunten fuera de `/audio/humano/`, y 0 oraciones con audio.
- 0 valores de variedad fuera de los permitidos y 0 licencias no comerciales o no declaradas.
- Muestra aleatoria de 40 entradas por variedad (todas, si había menos: 5 `norte` y 19 `sur`), comprobada contra las reglas: 0 fallos.

## Datos de evaluación (`evaluacion/`)

| Archivo | Contenido |
| --- | --- |
| `flores200-devtest-reservado.csv` | 1 012 oraciones trilingües nunca usadas para enseñar |
| `hoja-revision-quechua.csv`, `hoja-revision-aimara.csv` | 180 ejercicios ciegos por lengua del experimento del 29-09-2026. Contienen ítems y glosas de PanLex y deben regenerarse con `experimentos/` sobre el corpus nuevo |
| `clave-sistemas-*.csv` | correspondencia código → sistema (no se entrega a revisores) |
| `rubrica.md` | criterios y escala de revisión |
