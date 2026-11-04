"""Descarga las series del BCRP que usa la app y las guarda en data/.

La app lee solo estos CSV, así la demo funciona sin internet.
Uso: python scripts/actualizar_bcrp.py
"""
import csv
import json
import urllib.request
from pathlib import Path

BASE = "https://estadisticas.bcrp.gob.pe/estadisticas/series/api/{}/json/{}/{}/esp"
DATA = Path(__file__).resolve().parents[1] / "data"

TRIMESTRALES = {
    "precio_m2_corriente": "PD37946PQ",  # 12 distritos, S/ corrientes por m2
    "precio_m2_constante": "PD37945PQ",  # 12 distritos, S/ constantes de 2009
}
MENSUALES = {
    "tasa_hipotecaria_mn": "PN07848NM",  # bancos, soles, TEA
    "tasa_deposito_360_mn": "PN07815NM",  # bancos, soles, 360 días a más
    "tasa_referencia": "PD04722MM",
    "inflacion_12m": "PN01273PM",  # IPC Lima Metropolitana, var. % 12 meses
    "tipo_cambio": "PN01210PM",  # S/ por US$, promedio del periodo
}


def serie(codigo, desde, hasta):
    with urllib.request.urlopen(BASE.format(codigo, desde, hasta), timeout=30) as r:
        datos = json.loads(r.read().decode("utf-8-sig"))
    return [(p["name"], p["values"][0]) for p in datos["periods"] if p["values"][0] != "n.d."]


def guardar(nombre, columnas, desde, hasta):
    tablas = {col: dict(serie(cod, desde, hasta)) for col, cod in columnas.items()}
    periodos = list(dict.fromkeys(p for t in tablas.values() for p in t))
    with open(DATA / nombre, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["periodo", *columnas])
        for p in periodos:
            w.writerow([p, *(tablas[c].get(p, "") for c in columnas)])
    print(f"{nombre}: {len(periodos)} periodos, último {periodos[-1]}")


if __name__ == "__main__":
    DATA.mkdir(exist_ok=True)
    guardar("bcrp_trimestral.csv", TRIMESTRALES, "2013-1", "2026-4")
    guardar("bcrp_mensual.csv", MENSUALES, "2015-1", "2026-12")
