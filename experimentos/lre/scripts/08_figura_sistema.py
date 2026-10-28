from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image

base = Path(__file__).resolve().parents[1]
capturas = base / "entrada" / "capturas"
salida = base / "figuras"
matplotlib.rcParams.update({"font.family": "Arial", "font.size": 8, "pdf.fonttype": 42, "ps.fonttype": 42})
mm = 1 / 25.4
a = Image.open(capturas / "practica-recorte.png").convert("RGB")
a = a.crop((0, 0, a.width, int(a.height * 0.78)))
b = Image.open(capturas / "ficha-recorte.png").convert("RGB")
ancho = 174
alto_a = ancho * a.height / a.width
ancho_b = 112
alto_b = ancho_b * b.height / b.width
margen = 6
alto = alto_a + alto_b + 2 * margen
fig = plt.figure(figsize=(ancho * mm, alto * mm))
eje_a = fig.add_axes([0, (alto_b + margen) / alto, 1, alto_a / alto])
eje_b = fig.add_axes([(ancho - ancho_b) / 2 / ancho, 0, ancho_b / ancho, alto_b / alto])
for eje, imagen, letra in [(eje_a, a, "a"), (eje_b, b, "b")]:
    eje.imshow(imagen, interpolation="lanczos")
    eje.set_axis_off()
fig.text(0.002, (alto_b + margen + alto_a) / alto + 0.004, "a", fontsize=9, fontweight="bold", va="bottom")
fig.text(0.002, alto_b / alto + 0.004, "b", fontsize=9, fontweight="bold", va="bottom")
for ext in ["pdf", "png", "tiff"]:
    opciones = {"dpi": 600} if ext in ("png", "tiff") else {"dpi": 600}
    if ext == "tiff":
        opciones["pil_kwargs"] = {"compression": "tiff_lzw"}
    fig.savefig(salida / f"Fig5.{ext}", **opciones)
print(round(alto, 1), "mm de alto")
