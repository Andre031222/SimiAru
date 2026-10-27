# /// script
# requires-python = ">=3.11"
# dependencies = ["psycopg[binary]>=3.2"]
# ///
import csv
import re
import json
import os
import sqlite3
from pathlib import Path

import psycopg

raiz = Path(__file__).resolve().parents[2]
origen = raiz / "datos" / "curado" / "tinku-contenido.sqlite"
gramatica = raiz / "datos" / "fuentes" / "gramatica.json"
ejemplos = raiz / "datos" / "curado" / "gramatica_ejemplos.csv"
puno_formas = raiz / "datos" / "curado" / "puno_formas.csv"
puno_frases = raiz / "datos" / "curado" / "puno_frases.csv"
archivo_url = raiz / "api" / "datos" / "postgres.url"

tablas = {
    "fuentes": """id text primary key, nombre text, tipo text, lenguas text, url text, licencia text,
        redistribuible text, cita text, registros bigint""",
    "lexico": """id text primary key, lengua text, iso text, variante text, variedad text, variedad_evidencia text, forma text, glosa_es text,
        concepto text, categoria text, tema text, nivel text, ipa text, ejemplo text, ejemplo_es text,
        fuente_id text, fuente_url text, licencia text, estado_revision text, confianza bigint,
        audio text, audio_origen text, audio_credito text, soporte bigint, apta boolean, principal boolean, desplazada text""",
    "oraciones": """id text primary key, es text, quechua text, aimara text, nivel text, fuente_id text,
        licencia text, alineacion text, variedad_quechua text, variedad_aimara text, audio_es text, audio_quechua text, audio_aimara text""",
    "conceptos": "concepto text primary key, quechua_ids text, aimara_ids text, trilingue text, tema text",
    "temas": "id text primary key, nivel text, orden bigint",
}

VARIEDAD = (
    "alter table contenido.lexico alter column variedad set not null, alter column variedad set default '', "
    "alter column variedad_evidencia set default ''; "
    "alter table contenido.lexico add constraint lexico_variedad_valida check ((lengua = 'quechua' and variedad in ('qullaw', 'chanka', 'comun')) "
    "or (lengua = 'aimara' and variedad in ('norte', 'sur', 'comun')) or variedad = ''); "
    "create or replace function contenido.variedad_por_defecto() returns trigger language plpgsql as $$ begin "
    "if new.variedad is null or new.variedad = '' then "
    "new.variedad := case when new.lengua = 'aimara' then 'comun' when new.iso = 'quy' then 'chanka' "
    "when new.iso in ('quz', 'qxp', 'quh') then 'qullaw' else 'comun' end; "
    "new.variedad_evidencia := coalesce(nullif(new.variedad_evidencia, ''), 'iso_' || coalesce(new.iso, '')); end if; "
    "return new; end $$; "
    "create trigger lexico_variedad before insert or update of iso, variedad on contenido.lexico "
    "for each row execute function contenido.variedad_por_defecto()"
)

COMPARTIDA = (
    "alter table contenido.lexico add column compartida boolean not null default false; "
    "update contenido.lexico l set compartida = true where l.lengua = 'quechua' and (l.variedad_evidencia like 'ambas:%' "
    "or (l.variedad in ('chanka', 'qullaw') and exists (select 1 from contenido.lexico o where o.lengua = 'quechua' "
    "and o.variedad in ('chanka', 'qullaw') and o.variedad <> l.variedad and lower(o.forma) = lower(l.forma) and o.terminos && l.terminos)))"
)

indices = [
    "create index lexico_lengua_tema on contenido.lexico(lengua, tema, nivel)",
    "create index lexico_concepto on contenido.lexico(concepto)",
    "create index lexico_forma_trgm on contenido.lexico using gin (contenido.sin_tildes(forma) gin_trgm_ops)",
    "create index lexico_busqueda_trgm on contenido.lexico using gin (busqueda gin_trgm_ops)",
    "create index lexico_terminos on contenido.lexico using gin (terminos)",
    "create index lexico_forma on contenido.lexico(lengua, lower(forma))",
    "create index oraciones_nivel on contenido.oraciones(nivel, fuente_id)",
    "create index lexico_variedad on contenido.lexico(lengua, variedad)",
    "create index oraciones_variedad on contenido.oraciones(variedad_quechua, variedad_aimara)",
]


def url():
    return os.environ.get("TINKU_BD") or archivo_url.read_text(encoding="utf-8").strip()


def leer(tabla, columnas):
    with sqlite3.connect(origen) as db:
        return db.execute(f"select {', '.join(columnas)} from {tabla}").fetchall()


def cargar_gramatica(pg):
    if not gramatica.exists() or not ejemplos.exists():
        return
    datos = json.loads(gramatica.read_text(encoding="utf-8"))
    pg.execute("drop table if exists contenido.gramatica_ejemplos, contenido.gramatica cascade")
    pg.execute(
        "create table contenido.gramatica (id text primary key, lengua text, nivel text, orden bigint, titulo text, "
        "resumen text, explicacion text, modelos jsonb, sufijos text[], grupo text[], referencia text, estado text)"
    )
    pg.execute(
        "create table contenido.gramatica_ejemplos (id bigserial primary key, unidad text references contenido.gramatica(id), "
        "oracion_id text, posicion bigint, palabra text, raiz text, sufijo text, fuente_id text, antes text, despues text)"
    )
    for u in datos["unidades"]:
        pg.execute(
            "insert into contenido.gramatica values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
            (u["id"], u["lengua"], u["nivel"], u["orden"], u["titulo"], u["resumen"], u["explicacion"],
             psycopg.types.json.Jsonb(u["modelos"]), u["sufijos"], u["grupo"], datos["referencias"][u["lengua"]], datos["estado"]),
        )
    with ejemplos.open(encoding="utf-8") as h:
        filas = list(csv.DictReader(h))
    columnas = ["unidad", "oracion_id", "posicion", "palabra", "raiz", "sufijo", "fuente_id", "antes", "despues"]
    with pg.cursor().copy(f"copy contenido.gramatica_ejemplos ({', '.join(columnas)}) from stdin") as copia:
        for f in filas:
            copia.write_row([f[c] for c in columnas])
    pg.execute("create index gramatica_ejemplos_unidad on contenido.gramatica_ejemplos(unidad)")
    print(f"gramática: {len(datos['unidades'])} unidades, {len(filas)} ejemplos")


def palabras_puno(texto: str) -> list[str]:
    return re.findall(r"[a-zñáéíóúäëïöü']+", texto.lower().replace("’", "'").replace("´", "'"))


def cargar_puno(pg):
    pg.execute("alter table contenido.lexico add column en_puno boolean not null default false")
    if not puno_formas.exists() or not puno_frases.exists():
        return
    pg.execute("drop table if exists contenido.puno_formas, contenido.puno_frases")
    pg.execute("create table contenido.puno_formas (forma text primary key, frecuencia bigint, frases bigint)")
    pg.execute("create table contenido.puno_frases (id text primary key, texto text, palabras text[])")
    with puno_formas.open(encoding="utf-8") as h, pg.cursor().copy("copy contenido.puno_formas from stdin") as copia:
        for f in csv.DictReader(h):
            copia.write_row([f["forma"], f["frecuencia"], f["frases"]])
    with puno_frases.open(encoding="utf-8") as h, pg.cursor().copy("copy contenido.puno_frases from stdin") as copia:
        for f in csv.DictReader(h):
            copia.write_row([f["id"], f["texto"], palabras_puno(f["texto"])])
    pg.execute("create index puno_frases_palabras on contenido.puno_frases using gin (palabras)")
    marcadas = pg.execute(
        "update contenido.lexico l set en_puno = true from contenido.puno_formas p "
        "where l.lengua = 'quechua' and replace(lower(l.forma), %s, %s) = p.forma",
        ("’", "'"),
    ).rowcount
    pg.execute(
        "insert into contenido.fuentes values ('commonvoice_qxp', 'Common Voice: quechua de Puno (qxp)', "
        "'corpus oral transcrito', 'qxp', 'https://github.com/QuechuaBase/asr-puno-quechua', 'CC0 1.0', 'sí', "
        "'Mozilla Common Voice, quechua de Puno (qxp): frases leídas y habla espontánea, con particiones de QuechuaBase. CC0 1.0.', "
        "(select count(*) from contenido.puno_frases)) on conflict (id) do nothing"
    )
    print(f"quechua de Puno: {marcadas} entradas con forma atestiguada en Common Voice")


def main():
    with psycopg.connect(url()) as pg, pg.transaction():
        pg.execute("create extension if not exists unaccent")
        pg.execute("create extension if not exists pg_trgm")
        pg.execute("create schema if not exists contenido")
        pg.execute(
            "create or replace function contenido.sin_tildes(texto text) returns text language sql immutable parallel safe "
            "as $$ select public.unaccent('public.unaccent'::regdictionary, lower(coalesce(texto, ''))) $$"
        )
        pg.execute(
            "create or replace function contenido.terminos(glosa text) returns text[] language sql immutable parallel safe as $$ "
            "select coalesce(array_agg(distinct t), '{}') from (select trim(regexp_replace(regexp_replace(contenido.sin_tildes(x), "
            "'[¡!¿?.\"“”«»]', '', 'g'), '^((el|la|los|las|un|una|unos|unas|lo)\\s+)+', '')) t from regexp_split_to_table("
            "regexp_replace(coalesce(glosa, ''), '\\([^)]*\\)', '', 'g'), '[;,]| / ') x) s where t <> '' $$"
        )
        for tabla, definicion in tablas.items():
            columnas = [c.strip().split()[0] for c in definicion.split(",")]
            filas = leer(tabla, columnas)
            pg.execute(f"drop table if exists contenido.{tabla} cascade")
            pg.execute(f"create table contenido.{tabla} ({definicion})")
            with pg.cursor().copy(f"copy contenido.{tabla} ({', '.join(columnas)}) from stdin") as copia:
                for fila in filas:
                    copia.write_row(["" if v is None and tabla != "fuentes" else v for v in fila])
            print(f"{tabla}: {len(filas)}")
        pg.execute(
            "alter table contenido.lexico add column busqueda text generated always as "
            "(contenido.sin_tildes(forma || ' ' || glosa_es)) stored"
        )
        pg.execute("alter table contenido.lexico add column terminos text[] generated always as (contenido.terminos(glosa_es)) stored")
        pg.execute(VARIEDAD)
        pg.execute("delete from contenido.fuentes where id in ('panlex', 'minedu_americasnlp')")
        for sql in indices:
            pg.execute(sql)
        pg.execute(COMPARTIDA)
        cargar_puno(pg)
        print(f"palabras comunes a chanka y qullaw: {pg.execute('select count(*) from contenido.lexico where compartida').fetchone()[0]}")
        if pg.execute("select to_regclass('app.reportes') is not null").fetchone()[0]:
            aplicadas = pg.execute(
                "update contenido.lexico l set glosa_es = r.glosa_aplicada, concepto = r.concepto_aplicado, "
                "estado_revision = 'corregida_comunidad', confianza = greatest(l.confianza, 2), apta = true "
                "from (select distinct on (item_id) item_id, glosa_aplicada, concepto_aplicado from app.reportes "
                "where estado = 'aceptado' and glosa_aplicada <> '' order by item_id, resuelto desc) r where l.id = r.item_id"
            ).rowcount
            print(f"correcciones de la comunidad reaplicadas: {aplicadas}")
        if pg.execute("select to_regclass('app.grabaciones') is not null").fetchone()[0]:
            voces = pg.execute(
                "update contenido.lexico l set audio = '/grabaciones/' || g.archivo, audio_origen = 'hablante', audio_credito = g.credito "
                "from (select distinct on (lengua, lower(forma), item_id, variedad_lengua) item_id, variedad_lengua, lengua, forma, archivo, credito "
                "from app.grabaciones where estado = 'aprobada' order by lengua, lower(forma), item_id, variedad_lengua, resuelto desc) g "
                "where l.lengua = g.lengua and lower(l.forma) = lower(g.forma) and l.audio not like '/audio/humano/%' "
                "and (l.id = g.item_id or l.lengua = 'aimara' or (g.variedad_lengua <> '' and l.variedad = g.variedad_lengua))"
            ).rowcount
            print(f"grabaciones de hablantes reaplicadas: {voces}")
        cargar_gramatica(pg)
        pg.execute("analyze contenido.lexico")
        pg.execute("analyze contenido.oraciones")
    print("contenido cargado en PostgreSQL")


if __name__ == "__main__":
    main()
