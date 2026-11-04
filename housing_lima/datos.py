"""Carga los datos guardados en data/ y config/."""
import json
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
MESES_ES = {"Ene": 1, "Feb": 2, "Mar": 3, "Abr": 4, "May": 5, "Jun": 6,
            "Jul": 7, "Ago": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dic": 12}


def config() -> dict:
    return json.loads((RAIZ / "config" / "supuestos.json").read_text(encoding="utf-8"))


def distritos() -> pd.DataFrame:
    """Distritos de Urbania (may-2025) llevados a abr-2026 con la variación del índice de Lima."""
    d = pd.read_csv(RAIZ / "data" / "distritos_urbania.csv")
    idx = config()["indice_urbania"]
    d["precio_m2_base"] = d["precio_m2"]
    d["alquiler_100m2_base"] = d["alquiler_100m2"]
    d["precio_m2"] = d["precio_m2"] * idx["actual"]["precio_m2"] / idx["base"]["precio_m2"]
    d["alquiler_100m2"] = d["alquiler_100m2"] * idx["actual"]["alquiler_100m2"] / idx["base"]["alquiler_100m2"]
    return d


def bcrp_trimestral() -> pd.DataFrame:
    d = pd.read_csv(RAIZ / "data" / "bcrp_trimestral.csv")
    trimestre = d["periodo"].str.extract(r"T(\d)\.(\d\d)").astype(int)
    d["fecha"] = pd.to_datetime(dict(year=2000 + trimestre[1], month=trimestre[0] * 3 - 2, day=1))
    return d


def bcrp_mensual() -> pd.DataFrame:
    d = pd.read_csv(RAIZ / "data" / "bcrp_mensual.csv")
    partes = d["periodo"].str.extract(r"(\w{3})\.(\d{4})")
    d["fecha"] = pd.to_datetime(dict(year=partes[1].astype(int), month=partes[0].map(MESES_ES), day=1))
    return d


def ultimo(columna: str) -> tuple[float, str]:
    """Último valor disponible de una serie mensual y su periodo."""
    d = bcrp_mensual().dropna(subset=[columna])
    return float(d[columna].iloc[-1]), str(d["periodo"].iloc[-1])


def crecimiento_precios(anios: int, columna: str = "precio_m2_corriente") -> float:
    """Variación anual compuesta del precio por m2 en los últimos `anios`."""
    s = bcrp_trimestral()[columna]
    return float((s.iloc[-1] / s.iloc[-1 - anios * 4]) ** (1 / anios) - 1)
