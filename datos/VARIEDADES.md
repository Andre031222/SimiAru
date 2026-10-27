# Clasificación de variedades

eLOP no entrena un modelo. La base de conocimiento es el corpus curado, y cada entrada léxica y cada oración llevan una variedad asignada por reglas fijas y documentadas. El clasificador está en `scripts/variedades.py` y lo usa `scripts/02_construir_base.py`. Con las mismas fuentes, el resultado es siempre el mismo.

## Variedades

| Lengua | Valor de `variedad` | Ámbito |
| --- | --- | --- |
| Quechua | `qullaw` | Collao o Qullaw: Puno, Cusco, Arequipa, Moquegua, parte de Apurímac y el quechua boliviano (ISO quz, qxp y quh) |
| Quechua | `chanka` | Chanka: Ayacucho, Huancavelica y parte de Apurímac (ISO quy) |
| Quechua | `comun` | Forma atestiguada en las dos variedades o sin rasgos propios de ninguna (ver «neutra») |
| Aimara | `norte` | Norte del Titicaca: Huancané, Moho, San Antonio de Putina y parte de Azángaro |
| Aimara | `sur` | Chucuito, El Collao, Yunguyo, Puno, Moquegua, Tacna y el altiplano boliviano |
| Aimara | `comun` | Sin atestiguación de variedad en una fuente abierta, o atestiguada en ambas |

La columna `variedad_evidencia` registra la regla aplicada. Su valor sirve para filtrar con más o menos rigor.

## Evidencia usada

| Evidencia | Fuente y licencia | Uso |
| --- | --- | --- |
| Rasgos ortográficos del Collao | la propia forma | regla 1 |
| Etiqueta ISO de la fuente | Wikcionario (`quz`, `quh`, `quy`), Wiktionary en inglés (calificadores «Cusco» o «Bolivia») | Qullaw o Chanka según el código |
| Formas usadas por hablantes de Puno | Common Voice qxp, transcripciones (CC0) | atestiguación Qullaw |
| Corpus declarados Qullaw | DUDH en quechua cuzqueño y boliviano y Constitución de Bolivia (textos oficiales) | atestiguación Qullaw |
| Corpus declarados Chanka | AmericasNLI (quy, CC BY-SA 4.0), FLORES-200 dev (quy_Latn, CC BY-SA 4.0) | atestiguación Chanka. Solo cuentan las palabras sin rasgos del Collao |
| Listas comparativas por localidad | Blum et al. 2023, *crossandean* (CC BY 4.0) | Qullaw: Puno, Cuzco, Taquile, Arma (Arequipa), Chuquisaca, Cochabamba y Apolobamba. Chanka: Ayacucho y Huancavelica. Aimara: Huancané (norte) y Sullkatiti (sur) |

Para *crossandean*, la forma solo cuenta si la glosa española de la lista de Heggarty (2005) comparte al menos un término con la glosa de la entrada. Así, una coincidencia de escritura con otro significado no se toma como evidencia. Antes de comparar se transcribe la notación americanista: č → ch, λ → ll, χ → q en quechua y x en aimara, h → j en aimara salvo tras oclusiva, y la vocal seguida de «:» pasa a vocal con diéresis. En quechua, e y o se comparan como i y u. A los verbos se les quita el infinitivo (-y en quechua, -ña en aimara) para compararlos con las raíces de la lista.

## Reglas del quechua (entradas léxicas)

Las reglas se aplican en este orden. La primera que se cumple decide.

1. **Rasgo exclusivo del Collao → `qullaw`.** El chanka no tiene oclusivas glotalizadas ni aspiradas. Una forma con `p' t' ch' k' q'` (`eyectiva`) o con `ph th chh kh qh` (`aspirada`) es Qullaw aunque la fuente diga quy. Se excluye la secuencia *q + hina*: en *-qhina* la h empieza la palabra *hina* y no es aspiración. También se excluyen las palabras con letras ajenas al alfabeto quechua (b, c sin h, d, f, g, v, x, z), que suelen ser nombres o préstamos sin adaptar. Además, el progresivo *-sha-/-sya-* seguido de persona (por ejemplo, *kashan*, *rimashani*) indica Qullaw (`progresivo_sha`). El chanka usa *-chka-*. No se usa *-chka-* como prueba de chanka, porque el cuzqueño escrito también lo usa.
2. **Atestiguada en las dos variedades → `comun`** (`ambas:…`). La forma aparece en evidencia Qullaw y en evidencia Chanka: etiqueta ISO, corpus o lista comparativa.
3. **Atestiguada solo en una → esa variedad.**
4. **Sin evidencia → `comun` con evidencia `neutra`.** Son formas sin rasgos exclusivos del Collao y de fuentes que solo dicen «quechua» (Wikidata Q5218, Wiktionary `qu`, Wikcionario `qu`). No se pueden asignar a una variedad sin inventar. La API puede darles menos prioridad que a las `ambas:`.

Las etiquetas de fuentes que no son quechua sureño se descartan: entradas de Wiktionary marcadas Ecuador, Huallaga, Áncash, Junín, Kichwa, Santiago del Estero o Colombia, y de Wikcionario en códigos `qus`, `qug`, `qub`, `qup` o `quc`.

## Reglas del aimara (entradas léxicas)

- `norte`: la forma, o su raíz verbal, aparece en la lista de Huancané con un concepto compatible, y para ese concepto Sullkatiti da otra forma.
- `sur`: el caso inverso, con Sullkatiti frente a Huancané.
- `comun`: la forma aparece en ambas localidades para el mismo concepto (`ambas:crossandean`) o no hay atestiguación (`sin_atestiguar`). La lista aimara de IDS (Félix Layme Pairumani) no declara dialecto, así que sus entradas quedan como `comun` salvo que *crossandean* las atestigüe.

## Oraciones

`contenido.oraciones` tiene dos columnas: `variedad_quechua` (`qullaw`, `chanka` o vacía si no hay quechua) y `variedad_aimara` (`comun`, o vacía si no hay aimara).

- Las fuentes declaradas Chanka (AmericasNLI, FLORES-200 dev y DUDH quy) dan `chanka`. Si el texto contiene un rasgo exclusivo del Collao, la oración mezcla variedades: se elimina su lado quechua y se conservan el español y el aimara.
- Las fuentes declaradas Qullaw (DUDH quz y quh, Constitución de Bolivia) dan `qullaw`.
- Las fuentes sin variedad declarada (Constitución del Perú, Tatoeba) solo conservan el quechua si este tiene un rasgo del Collao, y entonces es `qullaw`. Si no lo tiene, se elimina el lado quechua. Así se descartan, entre otras, las oraciones de kichwa ecuatoriano que Tatoeba etiqueta como quechua.
- Ninguna fuente abierta de oraciones distingue aimara norteño y sureño. Por eso todo el aimara de las oraciones es `comun`.

## Comprobaciones

Al cargar la base, `07_cargar_postgres.py` impone una restricción `check`: el quechua solo admite `qullaw`, `chanka` o `comun`, y el aimara `norte`, `sur` o `comun`. Un disparador completa `variedad` a partir de `iso` cuando la API inserta un aporte de la comunidad sin variedad: aimara → `comun`, quy → `chanka`, quz/qxp/quh → `qullaw` y el resto → `comun`. La verificación del 25-10-2026 está en `INVENTARIO.md`. Ninguna fila `chanka` contiene eyectivas ni aspiradas.

## Limitaciones

- La atestiguación por corpus no distingue homógrafos ni sentidos. Una palabra común de las dos variedades queda como `chanka` si solo aparece en los corpus chanka, que son más pequeños que la colección de Puno. `chanka` significa «atestiguada en Chanka», no «exclusiva de Chanka».
- Common Voice qxp atestigua formas flexionadas. Para los verbos solo se buscan unas pocas terminaciones a partir de la raíz.
- *crossandean* ofrece unos 150 conceptos por localidad, con un hablante cada una. Por eso hay muy pocas entradas `norte` o `sur` en aimara, y su asignación refleja a esos hablantes.
- La regla de la aspirada puede fallar en compuestos donde una oclusiva final precede a una palabra que empieza por h, salvo *hina*, que ya está excluida.
- Las glosas del Wiktionary en inglés vienen de tablas de traducción donde el español y el quechua o el aimara están en la misma acepción. Siguen siendo un puente a través de esa acepción y no se han verificado con hablantes. Tienen confianza 2.
