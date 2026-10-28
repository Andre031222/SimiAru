import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

base = Path(__file__).resolve().parents[1]
entrada = Path(sys.argv[1]) if len(sys.argv) > 1 else base / "entrada" / "cuestionario.csv"
salida = Path(sys.argv[2]) if len(sys.argv) > 2 else base / "resultados" / "cuestionario"
salida.mkdir(parents=True, exist_ok=True)

datos = pd.read_csv(entrada)
sus = [f"sus{i}" for i in range(1, 11)]
tam = ["tam_utilidad", "tam_facilidad", "tam_intencion"]
if "version" in datos:
    datos = datos[datos["version"] == 2].copy()
ajustado = datos[sus] - 1
datos["sus_calculado"] = ajustado.sum(axis=1) * 2.5


def alfa(tabla: pd.DataFrame) -> float:
    k = tabla.shape[1]
    if len(tabla) < 2:
        return float("nan")
    return float(k / (k - 1) * (1 - tabla.var(axis=0, ddof=1).sum() / tabla.sum(axis=1).var(ddof=1)))


def media_ic(serie: pd.Series) -> dict:
    n = int(serie.count())
    m = float(serie.mean()) if n else float("nan")
    if n < 2:
        return {"n": n, "media": m, "de": float("nan"), "ic95": [float("nan"), float("nan")]}
    de = float(serie.std(ddof=1))
    t = stats.t.ppf(0.975, n - 1)
    return {"n": n, "media": m, "de": de, "ic95": [m - t * de / np.sqrt(n), m + t * de / np.sqrt(n)]}


resumen = {
    "participantes": int(len(datos)),
    "sus": media_ic(datos["sus_calculado"]),
    "alfa_sus": alfa(ajustado),
    "alfa_tam": alfa(datos[tam]),
    "tam": {c: media_ic(datos[c]) for c in tam},
    "por_lengua": {k: media_ic(g["sus_calculado"]) for k, g in datos.groupby("lengua")},
    "por_conocimiento": {k: media_ic(g["sus_calculado"]) for k, g in datos.groupby("conocimiento")},
}
datos.to_csv(salida / "cuestionario_con_sus.csv", index=False)
(salida / "resumen.json").write_text(json.dumps(resumen, ensure_ascii=False, indent=2, default=float), encoding="utf-8")
print(json.dumps(resumen, ensure_ascii=False, indent=2, default=float))
