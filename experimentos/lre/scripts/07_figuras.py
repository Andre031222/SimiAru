import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import FancyBboxPatch, Patch

from comun import FIGURAS, RESULTADOS

MM = 1 / 25.4
SIMPLE, DOBLE = 84 * MM, 174 * MM
NEGRO, GRIS = "#000000", "#6E6E6E"
OKABE = {"naranja": "#E69F00", "celeste": "#56B4E9", "verde": "#009E73", "amarillo": "#F0E442", "azul": "#0072B2",
         "bermellon": "#D55E00", "purpura": "#CC79A7", "gris": "#BBBBBB"}

plt.rcParams.update({
    "font.family": "sans-serif", "font.sans-serif": ["Arial", "Helvetica"], "font.size": 8, "axes.titlesize": 8,
    "axes.labelsize": 8, "xtick.labelsize": 8, "ytick.labelsize": 8, "legend.fontsize": 8,
    "axes.linewidth": 0.5, "xtick.major.width": 0.5, "ytick.major.width": 0.5, "xtick.major.size": 2.5, "ytick.major.size": 0,
    "lines.linewidth": 0.8, "hatch.linewidth": 0.4, "patch.linewidth": 0.4,
    "pdf.fonttype": 42, "ps.fonttype": 42, "svg.fonttype": "none",
    "axes.spines.top": False, "axes.spines.right": False, "legend.frameon": False,
    "savefig.dpi": 600, "figure.dpi": 150,
})


def exportar(fig, nombre: str):
    FIGURAS.mkdir(parents=True, exist_ok=True)
    for ext in ("pdf", "eps"):
        fig.savefig(FIGURAS / f"{nombre}.{ext}", format=ext)
    fig.savefig(FIGURAS / f"{nombre}.png", dpi=600)
    fig.savefig(FIGURAS / f"{nombre}.tiff", dpi=600, pil_kwargs={"compression": "tiff_lzw"})
    plt.close(fig)


def miles(n: int) -> str:
    return f"{n:,}".replace(",", " ")


CLASES = [
    ("CC0", OKABE["azul"], ""),
    ("CC BY", OKABE["celeste"], ""),
    ("CC BY-SA", OKABE["verde"], ""),
    ("CC BY-SA / CC BY / CC0 (por archivo)", OKABE["verde"], ".."),
    ("texto oficial / libre reproducción", OKABE["amarillo"], ""),
    ("no comercial", OKABE["bermellon"], "////"),
    ("no declarada", OKABE["naranja"], "\\\\\\\\"),
    ("voz sintética", OKABE["purpura"], "xxxx"),
]
ETIQUETA_CLASE = {"CC0": "CC0", "CC BY": "CC BY", "CC BY-SA": "CC BY-SA", "CC BY-SA / CC BY / CC0 (por archivo)": "CC BY-SA, CC BY or CC0 (per file)",
                  "texto oficial / libre reproducción": "Official text / free reproduction", "no comercial": "Non-commercial (CC BY-NC-SA)",
                  "no declarada": "No licence declared", "voz sintética": "Synthetic voice (NC or proprietary)"}
FUENTE = {"panlex": "PanLex", "minedu_americasnlp": "MINEDU", "wikcionario_es": "Wikcionario es", "wikidata_lexemas": "Wikidata",
          "wikcionario_en": "Wiktionary en", "ids": "IDS", "globalvoices_opus": "Global Voices", "constituciones": "Constitutions",
          "flores200": "FLORES", "americasnli": "AmericasNLI", "tatoeba": "Tatoeba", "dudh": "UDHR", "sintetico": "Synthetic",
          "lingua_libre": "Lingua Libre"}


def figura1():
    t = pd.read_csv(RESULTADOS / "licencias_por_fuente.csv")
    color = {c: (col, h) for c, col, h in CLASES}
    orden_clase = [c for c, _, _ in CLASES]
    grupos = [("léxico", "Lexicon entries"), ("oraciones", "Parallel sentences"), ("audio de palabras", "Word audio")]
    fig, ax = plt.subplots(figsize=(DOBLE, 92 * MM))
    y, ticks, etiquetas = 0, [], []
    for tipo, nombre in grupos:
        for momento, rotulo in (("antes", "before"), ("despues", "after")):
            g = t[(t.tipo == tipo) & (t[momento] > 0)].copy()
            g["o"] = g.clase_licencia.map(orden_clase.index)
            g = g.sort_values(["o", momento], ascending=[True, False])
            total = g[momento].sum()
            x = 0.0
            for r in g.itertuples():
                w = getattr(r, momento) / total
                col, h = color[r.clase_licencia]
                ax.barh(y, w, left=x, height=0.62, color=col, hatch=h, edgecolor="white", linewidth=0.6)
                if w >= 0.05:
                    oscuro = col in (OKABE["azul"], OKABE["bermellon"], OKABE["verde"])
                    texto = f"{FUENTE.get(r.fuente_id, r.fuente_id)} {w * 100:.0f}%" if w >= 0.14 else f"{w * 100:.0f}%"
                    ax.text(x + w / 2, y, texto, ha="center", va="center", fontsize=8,
                            color="white" if oscuro else NEGRO,
                            bbox=dict(boxstyle="square,pad=0.1", facecolor=col, edgecolor="none") if h else None)
                x += w
            ax.text(1.01, y, f"n = {miles(int(total))}", va="center", ha="left", fontsize=8)
            ticks.append(y)
            etiquetas.append(f"{nombre}, {rotulo}" if momento == "antes" else rotulo)
            y -= 0.8
        y -= 0.45
    ax.set_yticks(ticks, etiquetas)
    for lbl in ax.get_yticklabels():
        if lbl.get_text() == "after":
            lbl.set_text("after")
    ax.set_xlim(0, 1)
    ax.set_xticks([0, 0.25, 0.5, 0.75, 1], ["0", "25", "50", "75", "100"])
    ax.set_xlabel("Share of records (%)")
    ax.spines["left"].set_visible(False)
    presentes = [c for c in orden_clase if c in set(t.clase_licencia)]
    ax.legend(handles=[Patch(facecolor=color[c][0], hatch=color[c][1], edgecolor="white", label=ETIQUETA_CLASE[c]) for c in presentes],
              loc="upper center", bbox_to_anchor=(0.42, -0.17), ncol=3, handlelength=2.2, handleheight=1.2, columnspacing=1.2)
    fig.subplots_adjust(left=0.2, right=0.9, top=0.98, bottom=0.34)
    exportar(fig, "Fig1")


EVIDENCIA = [
    ("rasgo", "Collao-only feature (rule 1)", OKABE["azul"], ""),
    ("una", "Attested in one variety only", OKABE["celeste"], ""),
    ("ambas", "Attested in both varieties", OKABE["verde"], "...."),
    ("ninguna", "No variety evidence", OKABE["gris"], "////"),
]


def grupo_evidencia(regla: str) -> str:
    if regla.startswith("1"):
        return "rasgo"
    if "ambas" in regla or regla.startswith("2"):
        return "ambas"
    if "sin" in regla or regla.startswith("4"):
        return "ninguna"
    return "una"


def figura2():
    t = pd.read_csv(RESULTADOS / "clasificador_lexico.csv")
    t["ev"] = t.regla.map(grupo_evidencia)
    filas = {"quechua": [("qullaw", "Qullaw"), ("comun", "Common"), ("chanka", "Chanka")],
             "aimara": [("sur", "Southern"), ("comun", "Common"), ("norte", "Northern")]}
    fig, ejes = plt.subplots(1, 2, figsize=(DOBLE, 52 * MM), gridspec_kw={"wspace": 0.45})
    for ax, (lengua, titulo) in zip(ejes, (("quechua", "a  Quechua"), ("aimara", "b  Aymara"))):
        g = t[t.lengua == lengua]
        maximo = g.groupby("variedad").entradas.sum().max()
        for i, (v, nombre) in enumerate(filas[lengua]):
            x = 0
            h = g[g.variedad == v].groupby("ev").entradas.sum()
            for clave, _, col, hatch in EVIDENCIA:
                n = int(h.get(clave, 0))
                if n == 0:
                    continue
                ax.barh(-i, n, left=x, height=0.6, color=col, hatch=hatch, edgecolor="white", linewidth=0.6)
                if n / maximo > 0.12:
                    ax.text(x + n / 2, -i, miles(n), ha="center", va="center", fontsize=8,
                            color="white" if col == OKABE["azul"] else NEGRO,
                            bbox=dict(boxstyle="square,pad=0.1", facecolor=col, edgecolor="none") if hatch else None)
                x += n
            ax.text(x + maximo * 0.02, -i, miles(int(x)), va="center", ha="left", fontsize=8)
        ax.set_yticks([-i for i in range(3)], [n for _, n in filas[lengua]])
        ax.set_xlim(0, maximo * 1.18)
        ax.set_xlabel("Lexicon entries")
        ax.spines["left"].set_visible(False)
        ax.text(-0.24, 1.08, titulo, transform=ax.transAxes, fontsize=9, fontweight="bold", ha="left", va="bottom")
    fig.legend(handles=[Patch(facecolor=c, hatch=h, edgecolor="white", label=e) for _, e, c, h in EVIDENCIA],
               loc="lower center", ncol=4, bbox_to_anchor=(0.5, 0.0), handlelength=2.2, handleheight=1.2, columnspacing=1.0)
    fig.subplots_adjust(left=0.11, right=0.97, top=0.88, bottom=0.36)
    exportar(fig, "Fig2")


def figura3():
    t = pd.read_csv(RESULTADOS / "cobertura_basica.csv")
    listas = [("Swadesh-1955-100", "a  Swadesh 100"), ("Tadmor-2009-100", "b  Leipzig–Jakarta")]
    perfiles = [("quechua", "qullaw", "Quechua Qullaw"), ("quechua", "chanka", "Quechua Chanka"),
                ("aimara", "sur", "Aymara southern"), ("aimara", "norte", "Aymara northern")]
    estilos = {"antes_solo_fuentes_abiertas": ("Before, open-licence sources only", "^", "white", GRIS, 0.3),
               "antes": ("Before (all sources)", "o", "white", NEGRO, 0.1),
               "despues": ("After (variety + common)", "o", OKABE["azul"], OKABE["azul"], -0.1),
               "despues_sin_comun_no_atestiguado": ("After, unattested common excluded", "s", OKABE["naranja"], OKABE["naranja"], -0.3)}
    fig, ejes = plt.subplots(1, 2, figsize=(DOBLE, 62 * MM), sharey=True, gridspec_kw={"wspace": 0.12})
    for ax, (lista, titulo) in zip(ejes, listas):
        g = t[t.lista == lista]
        n = int(g.conceptos_con_glosa_es.iloc[0])
        for i, (lengua, perfil, _) in enumerate(perfiles):
            h = g[(g.lengua == lengua) & (g.perfil == perfil)].set_index("escenario")
            if i:
                ax.axhline(-i + 0.5, color="#DDDDDD", linewidth=0.3)
            for esc, (_, marca, relleno, borde, dy) in estilos.items():
                r = h.loc[esc]
                ax.plot([r.wilson_inf * 100, r.wilson_sup * 100], [-i + dy] * 2, color=borde, linewidth=0.6, zorder=2)
                ax.plot(r.proporcion * 100, -i + dy, marker=marca, markersize=4,
                        markerfacecolor=relleno, markeredgecolor=borde, markeredgewidth=0.7, linestyle="none", zorder=3)
        ax.set_xlim(0, 100)
        ax.set_xticks([0, 25, 50, 75, 100])
        ax.set_xlabel(f"Concepts with ≥ 1 usable form (%), n = {n}")
        ax.grid(axis="x", color="#DDDDDD", linewidth=0.3)
        ax.set_axisbelow(True)
        ax.spines["left"].set_visible(False)
        ax.text(0, 1.04, titulo, transform=ax.transAxes, fontsize=9, fontweight="bold", ha="left", va="bottom")
    ejes[0].set_yticks([-i for i in range(4)], [p[2] for p in perfiles])
    ejes[0].set_ylim(-3.5, 0.5)
    fig.legend(handles=[Line2D([], [], marker=m, markerfacecolor=f, markeredgecolor=b, color=b, linewidth=0.6, markersize=4.5, label=e)
                        for e, m, f, b, _ in estilos.values()],
               loc="lower center", ncol=2, bbox_to_anchor=(0.55, 0.0), columnspacing=1.5)
    fig.subplots_adjust(left=0.15, right=0.98, top=0.9, bottom=0.36)
    exportar(fig, "Fig3")


def figura4():
    fig, ax = plt.subplots(figsize=(DOBLE, 52 * MM))
    fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
    ax.set_xlim(0, 174)
    ax.set_ylim(0, 52)
    ax.axis("off")
    ancho, alto, base = 37, 26, 23
    cajas = [
        (1, base, "Open sources", "CC0, CC BY, CC BY-SA,\nofficial texts", OKABE["celeste"], ""),
        (46, base, "Variety classifier", "1 Collao-only feature\n2 attested in both\n3 attested in one\n4 none → common", OKABE["verde"], ""),
        (91, base, "Tagged base", "lexicon and sentences\nwith variety, evidence\nrule and usable flag", OKABE["amarillo"], ""),
        (136, base, "API filter", "learner variety + common\nfor targets, distractors\nand exams", OKABE["azul"], ""),
        (1, 0.6, "Removed", "non-commercial,\nundeclared licence,\nsynthetic voice", OKABE["bermellon"], "////"),
    ]
    for x, y, titulo, cuerpo, col, hatch in cajas:
        h = alto if y == base else 17.6
        ax.add_patch(FancyBboxPatch((x, y), ancho, h, boxstyle="round,pad=0,rounding_size=1.2", facecolor="white", edgecolor=col,
                                    linewidth=1.0, hatch=hatch))
        fondo = dict(boxstyle="square,pad=0.15", facecolor="white", edgecolor="none") if hatch else None
        if y == base:
            ax.add_patch(FancyBboxPatch((x, y + h - 2.5), ancho, 2.5, boxstyle="square,pad=0", facecolor=col, edgecolor=col, linewidth=0.5))
            ax.text(x + ancho / 2, y + h - 4.5, titulo, ha="center", va="top", fontsize=8, fontweight="bold")
            ax.text(x + ancho / 2, y + h - 9.5, cuerpo, ha="center", va="top", fontsize=8, linespacing=1.35)
        else:
            ax.text(x + ancho / 2, y + h - 2, titulo, ha="center", va="top", fontsize=8, fontweight="bold", bbox=fondo)
            ax.text(x + ancho / 2, y + h - 6, cuerpo, ha="center", va="top", fontsize=8, linespacing=1.3, bbox=fondo)
    for x in (1, 46, 91):
        ax.annotate("", xy=(x + ancho + 8, base + 11), xytext=(x + ancho + 0.5, base + 11),
                    arrowprops=dict(arrowstyle="-|>", color=NEGRO, linewidth=0.8, mutation_scale=8, shrinkA=0, shrinkB=0))
    ax.annotate("", xy=(1 + ancho / 2, 18.4), xytext=(1 + ancho / 2, base - 0.3),
                arrowprops=dict(arrowstyle="-|>", color=NEGRO, linewidth=0.8, mutation_scale=8, shrinkA=0, shrinkB=0))
    ax.text(3 + ancho / 2, 20.8, "licence audit", fontsize=8, va="center", ha="left")
    ax.text(46 + ancho / 2, base - 2, "evidence: the form itself, ISO tags,\nCommon Voice qxp, declared corpora,\ncrossandean lists",
            ha="center", va="top", fontsize=8, linespacing=1.3)
    exportar(fig, "Fig4")


if __name__ == "__main__":
    figura1()
    figura2()
    figura3()
    figura4()
