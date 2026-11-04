"""Comprar vs. alquilar: simulación mensual en soles nominales.

Ambos hogares gastan lo mismo cada mes. El que tiene el flujo más barato invierte
la diferencia, y quien alquila invierte además el efectivo que no usó en la compra.
Por eso la comparación se reduce a un solo número: el patrimonio de cada uno.
"""
from dataclasses import dataclass, replace

import numpy as np
import pandas as pd

MESES = 360  # siempre se simula a 30 años; el horizonte solo elige dónde leer


@dataclass(frozen=True)
class Caso:
    precio: float
    alquiler: float
    inicial_pct: float = 0.20
    plazo_anios: int = 20
    tea: float = 0.0747
    apreciacion: float = 0.025
    alza_alquiler: float = 0.03
    retorno: float = 0.0463
    inflacion: float = 0.025
    gastos_cierre: float = 0.01
    alcabala: float = 0.03
    uit: float = 5500
    paga_alcabala: bool = True
    predial_arbitrios: float = 0.004
    mantenimiento: float = 0.005
    seguro_desgravamen: float = 0.0004
    seguro_inmueble: float = 0.00025
    costo_venta: float = 0.03
    impuesto_ganancia: float = 0.05
    casa_habitacion: bool = True

    def con(self, **cambios) -> "Caso":
        return replace(self, **cambios)


def tasa_mensual(tasa_anual: float) -> float:
    return (1 + tasa_anual) ** (1 / 12) - 1


def cuota_mensual(deuda: float, tea: float, meses: int) -> float:
    """Cuota fija del sistema francés."""
    i = tasa_mensual(tea)
    if i == 0:
        return deuda / meses
    return deuda * i / (1 - (1 + i) ** -meses)


def efectivo_inicial(c: Caso) -> dict:
    alcabala = c.alcabala * max(0.0, c.precio - 10 * c.uit) if c.paga_alcabala else 0.0
    inicial = c.inicial_pct * c.precio
    gastos = c.gastos_cierre * c.precio
    return {"inicial": inicial, "gastos": gastos, "alcabala": alcabala,
            "total": inicial + gastos + alcabala}


def simular(c: Caso) -> pd.DataFrame:
    """Una fila por mes (0 a 360). El patrimonio supone vender la vivienda ese mes."""
    t = np.arange(MESES + 1)
    n = c.plazo_anios * 12
    deuda = c.precio * (1 - c.inicial_pct)
    i = tasa_mensual(c.tea)
    cuota_base = cuota_mensual(deuda, c.tea, n)

    # Saldo del crédito: fórmula cerrada del sistema francés.
    if i == 0:
        saldo = deuda * (1 - np.minimum(t, n) / n)
    else:
        saldo = deuda * ((1 + i) ** n - (1 + i) ** np.minimum(t, n)) / ((1 + i) ** n - 1)
    saldo_previo = np.r_[deuda, saldo[:-1]]

    valor = c.precio * (1 + c.apreciacion) ** (t / 12)
    cuota = np.where((t >= 1) & (t <= n), cuota_base, 0.0)
    interes = saldo_previo * i * (t >= 1) * (t <= n)
    seguros = (saldo_previo * c.seguro_desgravamen + valor * c.seguro_inmueble) * (t >= 1)
    tenencia = valor * (c.predial_arbitrios + c.mantenimiento) / 12 * (t >= 1)
    costo_comprar = cuota + seguros + tenencia
    # El alquiler sube una vez al año, al renovar el contrato.
    costo_alquilar = np.where(t >= 1, c.alquiler * (1 + c.alza_alquiler) ** ((t - 1) // 12), 0.0)

    r = tasa_mensual(c.retorno)
    cartera_inquilino = np.zeros(MESES + 1)
    cartera_comprador = np.zeros(MESES + 1)
    cartera_inquilino[0] = efectivo_inicial(c)["total"]
    for m in range(1, MESES + 1):
        dif = costo_comprar[m] - costo_alquilar[m]
        cartera_inquilino[m] = cartera_inquilino[m - 1] * (1 + r) + max(dif, 0.0)
        cartera_comprador[m] = cartera_comprador[m - 1] * (1 + r) + max(-dif, 0.0)

    neto_venta = valor * (1 - c.costo_venta)
    exonerado = c.casa_habitacion & (t >= 24)
    impuesto = np.where(exonerado, 0.0, c.impuesto_ganancia * np.maximum(neto_venta - c.precio, 0.0))
    patrimonio_comprar = neto_venta - saldo - impuesto + cartera_comprador

    return pd.DataFrame({
        "mes": t, "anio": t / 12, "valor": valor, "saldo": saldo, "cuota": cuota,
        "interes": interes, "seguros": seguros, "tenencia": tenencia,
        "costo_comprar": costo_comprar, "costo_alquilar": costo_alquilar,
        "cartera_comprador": cartera_comprador, "cartera_inquilino": cartera_inquilino,
        "costo_vender": valor * c.costo_venta, "impuesto": impuesto,
        "patrimonio_comprar": patrimonio_comprar, "patrimonio_alquilar": cartera_inquilino,
        "ventaja_comprar": patrimonio_comprar - cartera_inquilino,
    })


def ventaja(c: Caso, anios: int) -> float:
    """Patrimonio de quien compra menos el de quien alquila, en soles de ese año."""
    return float(simular(c)["ventaja_comprar"].iloc[anios * 12])


def mes_equilibrio(sim: pd.DataFrame) -> int | None:
    """Primer mes desde el cual comprar queda por delante hasta el final de los 30 años."""
    atras = np.flatnonzero(sim["ventaja_comprar"].to_numpy() < 0)
    if atras.size == 0:
        return 0
    return None if atras[-1] == MESES else int(atras[-1] + 1)
