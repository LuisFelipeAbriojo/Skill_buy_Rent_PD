"""Sensibilidad del resultado: tornado, mapa de calor, umbrales y distritos."""
import numpy as np
import pandas as pd

from .model import Caso, ventaja

# (parámetro, etiqueta, valor bajo, valor alto, formato de la etiqueta)
def _tramos(c: Caso) -> list:
    return [
        ("apreciacion", "Apreciación anual", c.apreciacion - 0.01, c.apreciacion + 0.01, "pct"),
        ("retorno", "Retorno de la inversión", c.retorno - 0.015, c.retorno + 0.015, "pct"),
        ("tea", "Tasa hipotecaria", c.tea - 0.01, c.tea + 0.01, "pct"),
        ("alza_alquiler", "Alza anual del alquiler", c.alza_alquiler - 0.01, c.alza_alquiler + 0.01, "pct"),
        ("alquiler", "Alquiler de hoy", c.alquiler * 0.9, c.alquiler * 1.1, "sol"),
        ("precio", "Precio de compra", c.precio * 0.9, c.precio * 1.1, "sol"),
        ("inicial_pct", "Cuota inicial", max(c.inicial_pct - 0.1, 0.05), c.inicial_pct + 0.1, "pct"),
        ("mantenimiento", "Mantenimiento mayor", max(c.mantenimiento - 0.003, 0.0), c.mantenimiento + 0.003, "pct"),
    ]


def _fmt(v: float, tipo: str) -> str:
    return f"{v * 100:.1f}%" if tipo == "pct" else f"S/ {v:,.0f}"


def tornado(c: Caso, anios: int) -> pd.DataFrame:
    """Cambia un parámetro a la vez. Ordenado de mayor a menor efecto."""
    filas = []
    for campo, etiqueta, bajo, alto, tipo in _tramos(c):
        v_bajo = ventaja(c.con(**{campo: bajo}), anios)
        v_alto = ventaja(c.con(**{campo: alto}), anios)
        filas.append({
            "parametro": etiqueta, "valor_bajo": _fmt(bajo, tipo), "valor_alto": _fmt(alto, tipo),
            "ventaja_bajo": v_bajo, "ventaja_alto": v_alto, "rango": abs(v_alto - v_bajo),
        })
    return pd.DataFrame(filas).sort_values("rango", ascending=False, ignore_index=True)


def mapa_calor(c: Caso, anios: int, apreciaciones=None, retornos=None) -> pd.DataFrame:
    """Ventaja de comprar por apreciación (columnas) y retorno (filas)."""
    apreciaciones = np.arange(0, 0.0601, 0.01) if apreciaciones is None else apreciaciones
    retornos = np.arange(0.03, 0.1101, 0.01) if retornos is None else retornos
    return pd.DataFrame(
        [[ventaja(c.con(apreciacion=float(a), retorno=float(r)), anios) for a in apreciaciones] for r in retornos],
        index=np.round(retornos, 4), columns=np.round(apreciaciones, 4),
    )


def umbral(c: Caso, anios: int, campo: str, bajo: float, alto: float) -> float | None:
    """Valor de `campo` en el que comprar y alquilar empatan (bisección)."""
    v_bajo = ventaja(c.con(**{campo: bajo}), anios)
    v_alto = ventaja(c.con(**{campo: alto}), anios)
    if v_bajo * v_alto > 0:
        return None
    for _ in range(40):
        medio = (bajo + alto) / 2
        v_medio = ventaja(c.con(**{campo: medio}), anios)
        if v_bajo * v_medio <= 0:
            alto = medio
        else:
            bajo, v_bajo = medio, v_medio
    return (bajo + alto) / 2


def por_distrito(c: Caso, anios: int, distritos: pd.DataFrame, m2: float) -> pd.DataFrame:
    """Mismos supuestos y metraje en cada distrito; cambian el precio y el alquiler."""
    d = distritos.copy()
    d["precio"] = d["precio_m2"] * m2
    d["alquiler"] = d["alquiler_100m2"] * m2 / 100
    d["rentabilidad"] = d["alquiler"] * 12 / d["precio"]
    d["ventaja"] = [
        ventaja(c.con(precio=float(p), alquiler=float(a)), anios)
        for p, a in zip(d["precio"], d["alquiler"])
    ]
    return d.sort_values("ventaja", ascending=False, ignore_index=True)
