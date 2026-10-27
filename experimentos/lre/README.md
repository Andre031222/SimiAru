# Evaluación para *Language Resources and Evaluation*

Esta carpeta reúne la evaluación del artículo sobre eLOP para la sección de lenguas con pocos recursos de *Language Resources and Evaluation* (Springer). Todas las cifras salen de las bases de datos y se escriben en `resultados/`. Ningún número del artículo debe escribirse a mano: se copia de los CSV o de `resultados/resumen.json`.

Por regla del proyecto, el código no lleva comentarios. Lo que hace cada script se explica aquí.

## Contenido

| Carpeta | Qué contiene |
| --- | --- |
| `entrada/` | Volcado del corpus anterior (`corpus-anterior.dump`) y listas de conceptos (`listas/`). Está en `.gitignore` y no se redistribuye |
| `scripts/` | Análisis, figuras y kit de revisión |
| `resultados/` | CSV de cada análisis y `resumen.json` con las cifras clave |
| `figuras/` | Fig1 a Fig4 en PDF, EPS, PNG y TIFF, y `leyendas.md` |
| `revision/` | Kit de validación con hablantes |

## Datos de partida

- **Corpus actual:** esquema `contenido` de PostgreSQL (URL en `api/datos/postgres.url`), cargado el 25-10-2026 con `datos/scripts/07_cargar_postgres.py`. Es el mismo que describe `datos/INVENTARIO.md`.
- **Corpus anterior:** `entrada/corpus-anterior.dump`, volcado del 25-10-2026 a las 08:06, antes de retirar PanLex, MINEDU y la voz sintética. El volcado también contiene datos de usuarios (esquema `app`). Solo se restaura el esquema `contenido`, en una base local nueva, así:

```bash
createdb elop_anterior
psql -d elop_anterior -c "create extension if not exists pg_trgm; create extension if not exists unaccent; create schema contenido;"
pg_restore -d elop_anterior -n contenido --no-owner --no-acl experimentos/lre/entrada/corpus-anterior.dump
```

  Hay que crear el esquema a mano porque `pg_restore -n` no lo crea. Los scripts leen la base anterior en `postgresql:///elop_anterior` (variable `ELOP_BD_ANTERIOR`) y la actual en `api/datos/postgres.url` (variable `ELOP_BD`). Ningún script lee el esquema `app`.

- Las cifras del volcado difieren un poco de `git show dfbf6b4:01-datos/INVENTARIO.md` (29-09-2026) en el audio: el volcado tiene 57 492 entradas con audio (1 957 de hablante y 55 535 sintéticas) y el inventario de septiembre daba 53 188. Se usa el volcado porque es el estado real del sistema antes del cambio. Léxico (58 265) y oraciones (15 583) coinciden con ese inventario.

## Listas de conceptos básicos

Descargadas el 27-10-2026 de Concepticon, `concepticon-data` versión v3.4.0 (https://github.com/concepticon/concepticon-data/tree/v3.4.0/concepticondata/conceptlists), licencia CC BY 4.0 (declarada en `metadata.json` y `.zenodo.json` del repositorio, copiados en `entrada/listas/`). Cita: List, J.-M. et al., *Concepticon*, versión 3.4.0.

| Archivo | Uso |
| --- | --- |
| `Swadesh-1955-100.tsv` | lista evaluada (Swadesh 100) |
| `Tadmor-2009-100.tsv` | lista evaluada (Leipzig–Jakarta) |
| `Swadesh-1952-200.tsv` | lista evaluada (Swadesh 200, solo en CSV) |
| `Swadesh-1961-100.tsv`, `Key-2016-1310.tsv`, `Huber-1992-375.tsv`, `Rowe-1954-232.tsv`, `Lastra-1986-381.tsv` | glosas en español, unidas por `CONCEPTICON_ID` |

Las listas de Swadesh y Leipzig–Jakarta solo tienen glosa inglesa. Su glosa española se toma de las listas de Concepticon que sí la tienen, unidas por el identificador de concepto. No se tradujo nada a mano. Los conceptos sin glosa española quedan fuera del denominador: 2 de Swadesh 100 (*rain*, *warm*), 4 de Leipzig–Jakarta (*arm/hand*, *leg/foot*, *to know*, *to hide*) y 10 de Swadesh 200 (lista completa en `resultados/cobertura_mapa_conceptos_es.csv`, columna `incluido`). No se usa Heggarty-2005-150, porque el clasificador ya usa sus glosas. Las sumas SHA-256 las imprime `scripts/00_descargar_listas.sh`.

**Circularidad:** las glosas españolas del IDS aimara vienen de Key-2016-1310, la misma lista que da glosas a la evaluación. Por eso se repite todo el análisis sin Key-2016-1310 (`resultados/cobertura_basica_sin_key_2016_1310.csv`; quedan 97, 79 y 176 conceptos).

## Análisis

### 1. Auditoría de licencias (`01_licencias.py`)

Cuenta, por fuente y tipo de registro (léxico, oraciones, audio de palabras, audio de oraciones y evidencia), los registros antes y después, la licencia, su clase, si permite uso comercial, si la fuente se mantuvo, es nueva o se retiró, y el motivo. El uso comercial se marca «no» para las licencias no comerciales, las no declaradas y la voz sintética. Las licencias de textos oficiales y de libre reproducción se marcan «sí». El audio sintético antes no tenía fuente en `contenido.fuentes`; se cuenta por `audio_origen = 'sintetico'`.

Salida: `resultados/licencias_por_fuente.csv`.

### 2. Fugas de variedad antes y después (`02_fugas_variedad.py`)

Aplica al corpus anterior y al actual los mismos rasgos del Collao que usa el clasificador, importando `rasgo_qullaw` de `datos/scripts/variedades.py` (eyectivas, aspiradas y progresivo *-sha-/-sya-*). Mide:

- entradas etiquetadas `chanka` con rasgo del Collao (antes la etiqueta venía del código ISO: quy → chanka);
- entradas de aimara con etiqueta norte o sur;
- entradas de quechua cuya fuente no declara variedad (ISO `qu` o `que`). Antes, `qu` se etiquetaba como `qullaw` sin evidencia; ahora esas entradas pasan por el clasificador, y las que no tienen evidencia quedan `comun`/`neutra`, que también se informa;
- oraciones con quechua de fuentes declaradas Chanka que contienen rasgos del Collao. Antes las oraciones no tenían variedad; se usa la variedad declarada por la fuente (AmericasNLI, FLORES-200 y MINEDU: chanka; DUDH: quz; Constituciones: mezcla de que y quh; Tatoeba: sin declarar).

Todas las medidas se dan sobre todas las entradas y sobre las aptas (`apta`), que son las que llegan a los ejercicios.

Salidas: `resultados/fugas_variedad_lexico.csv`, `resultados/fugas_variedad_oraciones.csv`.

### 3. Estadística del clasificador (`03_clasificador.py`)

Cruza lengua, variedad, regla aplicada (1 a 4 del quechua y las tres del aimara de `datos/VARIEDADES.md`), tipo de evidencia y fuente. Cuenta también cuántas entradas tienen cada familia de evidencia (rasgo, etiqueta ISO, Common Voice qxp, corpus Qullaw, corpus Chanka, DUDH, *crossandean*). El token `dudh` se informa aparte porque el clasificador usa el mismo origen para la DUDH quz, quh y quy. Incluye dos controles: entradas con rasgo del Collao que no son `qullaw` y entradas cuyo rasgo recalculado no coincide con la evidencia guardada.

Salidas: `resultados/clasificador_lexico.csv`, `clasificador_evidencias_familia.csv`, `clasificador_evidencias_detalle.csv`, `clasificador_oraciones.csv`.

### 4. Cobertura del vocabulario básico (`04_cobertura.py`)

Un concepto está cubierto para un perfil si existe al menos una entrada apta de esa lengua, con variedad del perfil o `comun`, cuya glosa comparte un término con la glosa española del concepto. Los términos se normalizan con `variedades.terminos` (minúsculas, sin tildes, sin artículos, separando por `;`, `,` y `/`). La coincidencia es exacta por término: *comer algo* no cuenta como *comer*. Por eso la cobertura es una cota inferior.

Escenarios:

| Escenario | Qué entradas cuentan |
| --- | --- |
| `antes` | corpus anterior con sus etiquetas ISO. Quechua Qullaw = `qullaw` + `comun`; Chanka = `chanka` + `comun`. El aimara no tenía variedad, así que ambos perfiles usan todo el aimara |
| `antes_solo_fuentes_abiertas` | lo mismo, solo Wikcionario y Wikidata, las fuentes abiertas que ya había |
| `despues` | corpus actual, variedad del perfil + `comun` |
| `despues_sin_comun_no_atestiguado` | igual, sin `comun` con evidencia `neutra` o `sin_atestiguar` |

Intervalos de Wilson al 95 %. Salidas: `resultados/cobertura_basica.csv` (agregado), `cobertura_basica_por_concepto.csv` (concepto a concepto, con hasta tres formas de ejemplo), `cobertura_mapa_conceptos_es.csv` (glosas españolas usadas) y sus versiones `_sin_key_2016_1310`.

### 5. Comprobación del sistema (`05_sistema.py`)

Usa la API local (`http://127.0.0.1:3000`, variable `TINKU_URL`) con la cuenta de demostración. Para cada perfil cambia la variedad del usuario de demostración con `PATCH /api/perfil` y pide sesiones de `POST /api/practica` (30 ejercicios cada una) hasta reunir al menos 3 000 ejercicios léxicos (variable `EJERCICIOS`). El tema se elige al azar entre los de la lengua y «todos»; el enfoque, entre ninguno (dos veces más probable), `puente`, `significado` y `escuchar`. Al terminar, aunque falle, devuelve la cuenta de demostración a su variedad original (qullaw y sur). Los ejercicios no se registran como respuestas.

Perfiles: quechua Qullaw (aimara sur), quechua Chanka (aimara norte), aimara sur (quechua Qullaw) y aimara norte (quechua Chanka). La variedad de la otra lengua solo afecta a los ejercicios *puente*.

Para cada ejercicio se comprueba:

- **objetivo fuera:** la variedad de la entrada objetivo no es la del perfil ni `comun`;
- **distractores fuera:** un distractor es una forma (o una glosa en los ejercicios de reconocer) que no corresponde a ninguna entrada aprendible de la variedad del perfil o `comun`. En *puente* se mide contra la variedad del perfil en la otra lengua, y también la respuesta correcta;
- **audio de hablante:** el ejercicio trae audio con `audio_origen = 'hablante'`; se cuenta además cualquier audio que no sea de hablante.

Como control de que la prueba detecta fugas, se mide también cuántos objetivos y distractores quedarían fuera si el perfil fuera el opuesto (Qullaw ↔ Chanka, sur ↔ norte). La proporción de audio se da para todos los enfoques y solo para «sin enfoque», porque el enfoque `escuchar` elige a propósito entradas con audio. La API ordena con `random()` de PostgreSQL sin semilla, así que los conteos cambian un poco en cada ejecución; las proporciones de fuga deben seguir en 0.

Salidas: `resultados/sistema_ejercicios.csv` (un ejercicio por fila) y `resultados/sistema_resumen.csv`.

### 6. Kit de validación con hablantes (`06_kit_revision.py`)

Muestra aleatoria estratificada con semilla 2027:

- **Quechua, 200 entradas aptas:** 50 `qullaw`, 50 `chanka`, 50 `comun` atestiguadas en ambas (`ambas:`) y 50 `comun` neutras. Dentro de cada clase, el reparto entre fuentes es lo más parejo posible.
- **Aimara, 100 entradas:** todas las `norte` (5) y `sur` (19), aunque alguna no sea apta, y 76 `comun` aptas, 38 atestiguadas en ambas localidades y 38 sin atestiguar, repartidas entre fuentes.

Archivos:

| Archivo | Para quién |
| --- | --- |
| `revision/hoja-quechua.xlsx`, `revision/hoja-aimara.xlsx` | revisores. Orden aleatorio, código neutro (Q001…, A001…), sin variedad predicha ni fuente. Listas desplegables para la glosa (sí/parcial/no) y la variedad (Collao/Chanka/ambas/no sé o norteño/sureño/ambos/no sé). Pestaña con datos del revisor |
| `revision/clave-oculta.csv` | equipo. Código, identificador de léxico, fuente, variedad predicha, evidencia, clase y tamaños del estrato (para ponderar). **No se entrega a los revisores** |
| `revision/rubrica.md` | instrucciones para revisores |
| `revision/consentimiento.md` | consentimiento informado |

Cada hoja la llenan dos hablantes por separado. Luego:

```bash
cd experimentos/lre
uv run --with pandas --with openpyxl python scripts/analizar_revision.py --lengua quechua \
  --clave revision/clave-oculta.csv --r1 revision/respuestas/quechua-R1.xlsx --r2 revision/respuestas/quechua-R2.xlsx \
  --salida resultados/revision
```

`analizar_revision.py` calcula:

- kappa de Cohen entre revisores para la glosa y para la variedad (con y sin «no sé»), en total y por clase;
- consenso: la respuesta en que coinciden los dos revisores. Los desacuerdos y los «no sé» quedan fuera del consenso de variedad;
- exactitud de la variedad predicha frente al consenso (qullaw ↔ Collao, chanka ↔ Chanka, comun ↔ ambas; norte ↔ norteño, sur ↔ sureño, comun ↔ ambos) y una exactitud «compatible», que también acepta una predicción de una sola variedad cuando el consenso dice «ambas»;
- proporción de glosas correctas (consenso «sí») y correctas o parciales, y la de cada revisor;
- intervalos de Wilson al 95 % para todas las proporciones.

Escribe `revision-<lengua>.json`, `revision-<lengua>-tabla.csv` y `revision-<lengua>-items.csv` en `--salida`. Se probó con datos simulados en una carpeta temporal (respuestas idénticas a la predicción: kappa 1 y exactitud 1; respuestas con ruido: valores intermedios) y con un caso calculado a mano (kappa 0,5; Wilson 8/10 = 0,490–0,943). Ningún resultado simulado está en `resultados/`.

## Figuras (`07_figuras.py`)

Ancho de doble columna (174 mm), Arial de 8 pt (9 pt en las letras de panel), líneas de al menos 0,4 pt, paleta Okabe–Ito con tramas para leerse en blanco y negro, sin título interno. Cada figura se exporta en PDF y EPS con fuentes TrueType incrustadas (`pdf.fonttype = 42`) y en PNG y TIFF (LZW) a 600 ppp.

| Figura | Contenido | Datos |
| --- | --- | --- |
| Fig1 (174 × 92 mm) | composición por fuente y clase de licencia, antes y después, para léxico, oraciones y audio | `licencias_por_fuente.csv` |
| Fig2 (174 × 52 mm) | entradas por variedad y tipo de evidencia, quechua y aimara | `clasificador_lexico.csv` |
| Fig3 (174 × 62 mm) | cobertura de Swadesh 100 y Leipzig–Jakarta por perfil, cuatro escenarios con IC de Wilson | `cobertura_basica.csv` |
| Fig4 (174 × 52 mm) | diagrama del proceso | — |

Las leyendas están en `figuras/leyendas.md`.

## Cómo reproducir

Requisitos: PostgreSQL local con la base actual y `elop_anterior` restaurada, `uv`, y la API corriendo en `127.0.0.1:3000` con `TINKU_DEMO=1` (si no lo está: `cd api && TINKU_DEMO=1 ./target/release/elop-api &`, y detenerla al terminar).

```bash
cd experimentos/lre
./scripts/00_descargar_listas.sh
./scripts/ejecutar.sh
```

`ejecutar.sh` corre los scripts 01 a 07 con `uv run --with pandas --with psycopg[binary] --with openpyxl --with matplotlib`. Cada uno también se puede ejecutar solo, desde `scripts/`. Cada script actualiza su propia clave en `resultados/resumen.json`.

## Limitaciones

- La cobertura depende de que la glosa coincida término a término; no mide si la forma es la más usual.
- Antes, el aimara no tenía variedad, de modo que la cobertura «antes» de los dos perfiles aimara es la misma.
- La comprobación del sistema mide la API de práctica léxica (`/api/practica`), no las lecciones, el examen ni los retos, que usan el mismo filtro (`Variedades::lexico`).
- El kit de revisión todavía no tiene respuestas: no hay cifras de exactitud con hablantes.
