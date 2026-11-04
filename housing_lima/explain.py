"""Convierte el resultado del modelo en frases para la página."""
from .analysis import umbral
from .model import Caso, efectivo_inicial, mes_equilibrio


def soles(x: float) -> str:
    # Espacio duro para que "S/" no se separe del monto; abs evita mostrar "-0".
    return f"{'−' if round(x) < 0 else ''}S/ {abs(x):,.0f}"


def pct(x: float, dec: int = 1) -> str:
    return f"{x * 100:.{dec}f}%"


def anios_texto(n: int) -> str:
    return "1 año" if n == 1 else f"{n} años"


def veredicto(sim, anios: int) -> str:
    v = float(sim["ventaja_comprar"].iloc[anios * 12])
    ganador = "comprar" if v >= 0 else "alquilar e invertir"
    return f"A {anios_texto(anios)}, {ganador} te deja unos {soles(round(abs(v), -3))} más"


def equilibrio_texto(sim) -> str:
    m = mes_equilibrio(sim)
    if m is None:
        return "Más de 30 años"
    if m == 0:
        return "Desde el inicio"
    return f"Año {m / 12:.1f}"


def razones(c: Caso, sim, anios: int) -> list[str]:
    fila = sim.iloc[anios * 12]
    primer = sim.iloc[1]
    efectivo = efectivo_inicial(c)["total"]
    dif = primer["costo_comprar"] - primer["costo_alquilar"]
    if dif >= 0:
        flujo = (f"**El primer mes, comprar cuesta {soles(dif)} más.** Son {soles(primer['costo_comprar'])} "
                 f"entre cuota, seguros y gastos, contra {soles(primer['costo_alquilar'])} de alquiler. "
                 "Quien alquila invierte esa diferencia.")
    else:
        flujo = (f"**El primer mes, comprar cuesta {soles(-dif)} menos.** Son {soles(primer['costo_comprar'])} "
                 f"entre cuota, seguros y gastos, contra {soles(primer['costo_alquilar'])} de alquiler. "
                 "Quien compra invierte esa diferencia.")
    salida = (f"**Quien alquila parte con {soles(efectivo)} invertidos** y llega a "
              f"{soles(fila['patrimonio_alquilar'])} al año {anios}. Quien compra llega a "
              f"{soles(fila['patrimonio_comprar'])} si vende ese año.")

    tope = umbral(c, anios, "apreciacion", -0.05, 0.15)
    if tope is None:
        empate = "**Ninguna apreciación entre −5% y 15% anual cambia el resultado.**"
    else:
        empate = (f"**El empate está en {pct(tope)} de apreciación anual.** "
                  f"Por encima conviene comprar y por debajo, alquilar. "
                  f"Este escenario supone {pct(c.apreciacion)}.")
    return [flujo, salida, empate]


def casi_empate(sim, anios: int) -> bool:
    """La diferencia es menor al 5% del patrimonio: no alcanza para recomendar."""
    fila = sim.iloc[anios * 12]
    return abs(fila["ventaja_comprar"]) < 0.05 * max(fila["patrimonio_comprar"], fila["patrimonio_alquilar"])
