"""Lanzador de la skill buy-vs-rent: corre el motor housing_lima y devuelve JSON.

Tasas y porcentajes se escriben en %: --tea 7.47 significa 7.47%.
Uso desde la raíz del proyecto:
    .venv/Scripts/python .claude/skills/buy-vs-rent/scripts/hl.py analizar --distrito Lince --m2 70
    .venv/Scripts/python .claude/skills/buy-vs-rent/scripts/hl.py distritos --m2 70 --anios 10
    .venv/Scripts/python .claude/skills/buy-vs-rent/scripts/hl.py app
"""
import argparse
import json
import subprocess
import sys
import unicodedata
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(RAIZ))

from housing_lima import analysis, datos, explain  # noqa: E402
from housing_lima.model import cuota_mensual, efectivo_inicial, mes_equilibrio, simular  # noqa: E402


class ErrorEntrada(Exception):
    pass


def _normal(texto: str) -> str:
    sin_tildes = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return sin_tildes.lower().strip()


def buscar_distrito(nombre: str):
    """Acepta nombres parciales ("surco", "jesus maria"); rechaza los ambiguos o desconocidos."""
    tabla = datos.distritos()
    buscado = _normal(nombre)
    aciertos = tabla[tabla["distrito"].map(lambda d: buscado in _normal(d))] if buscado else tabla.iloc[:0]
    if len(aciertos) == 1:
        return aciertos.iloc[0]
    disponibles = ", ".join(tabla["distrito"])
    if aciertos.empty:
        raise ErrorEntrada(f"Distrito sin datos: '{nombre}'. Pide precio y alquiler del aviso. Disponibles: {disponibles}.")
    raise ErrorEntrada(f"'{nombre}' es ambiguo: {', '.join(aciertos['distrito'])}.")


def _texto(s: str) -> str:
    return s.replace(" ", " ")


def _cambios(a) -> dict:
    """Solo los supuestos que se pidieron cambiar; lo demás queda en el caso base."""
    cambios = {}
    for campo, valor in (("inicial_pct", a.inicial), ("tea", a.tea), ("apreciacion", a.apreciacion),
                         ("alza_alquiler", a.alza_alquiler), ("retorno", a.retorno),
                         ("mantenimiento", a.mantenimiento), ("costo_venta", a.costo_venta)):
        if valor is not None:
            cambios[campo] = valor / 100
    if a.plazo is not None:
        cambios["plazo_anios"] = a.plazo
    if a.primera_venta:
        cambios["paga_alcabala"] = False
    if a.no_casa_habitacion:
        cambios["casa_habitacion"] = False
    return cambios


def _validar(a):
    if not 1 <= a.anios <= 30:
        raise ErrorEntrada("--anios debe estar entre 1 y 30.")
    if a.plazo is not None and not 1 <= a.plazo <= 30:
        raise ErrorEntrada("--plazo debe estar entre 1 y 30.")
    if a.inicial is not None and not 0 <= a.inicial < 100:
        raise ErrorEntrada("--inicial debe estar entre 0 y 100.")
    if a.m2 is not None and a.m2 <= 0:
        raise ErrorEntrada("--m2 debe ser mayor que 0.")


def analizar(a) -> dict:
    _validar(a)
    if a.precio is not None and a.precio <= 0 or a.alquiler is not None and a.alquiler <= 0:
        raise ErrorEntrada("--precio y --alquiler deben ser mayores que 0.")
    fila = buscar_distrito(a.distrito) if a.distrito else None
    if a.precio is None or a.alquiler is None:
        if fila is None or a.m2 is None:
            raise ErrorEntrada("Indica --precio y --alquiler, o bien --distrito y --m2 para estimar lo que falte.")
    precio = a.precio if a.precio is not None else float(fila["precio_m2"]) * a.m2
    alquiler = a.alquiler if a.alquiler is not None else float(fila["alquiler_100m2"]) * a.m2 / 100

    caso = datos.caso(precio, alquiler, **_cambios(a))
    sim = simular(caso)
    final = sim.iloc[a.anios * 12]
    primer = sim.iloc[1]
    entrada = efectivo_inicial(caso)
    equilibrio = mes_equilibrio(sim)
    idx = datos.config()["indice_urbania"]

    def empate(campo, bajo, alto):
        v = analysis.umbral(caso, a.anios, campo, bajo, alto)
        return None if v is None else round(v * 100, 2)

    alquiler_empate = analysis.umbral(caso, a.anios, "alquiler", caso.alquiler * 0.2, caso.alquiler * 4)
    tornado = analysis.tornado(caso, a.anios).head(3)
    return {
        "veredicto": _texto(explain.veredicto(sim, a.anios)),
        "casi_empate": bool(explain.casi_empate(sim, a.anios)),
        "ventaja_comprar": round(float(final["ventaja_comprar"])),
        "ventaja_comprar_soles_de_hoy": round(float(final["ventaja_comprar"]) / (1 + caso.inflacion) ** a.anios),
        "razones": [_texto(r) for r in explain.razones(caso, sim, a.anios)],
        "origen": {
            "distrito": None if fila is None else fila["distrito"],
            "precio": "dato del usuario" if a.precio is not None else f"estimado: Urbania {idx['base']['mes']} ajustado a {idx['actual']['mes']}",
            "alquiler": "dato del usuario" if a.alquiler is not None else f"estimado: Urbania {idx['base']['mes']} ajustado a {idx['actual']['mes']}",
        },
        "entradas": {
            "precio": round(caso.precio), "alquiler_mensual": round(caso.alquiler), "anios": a.anios,
            "inicial_pct": round(caso.inicial_pct * 100, 2), "plazo_anios": caso.plazo_anios,
            "tea_pct": round(caso.tea * 100, 2), "apreciacion_pct": round(caso.apreciacion * 100, 2),
            "alza_alquiler_pct": round(caso.alza_alquiler * 100, 2), "retorno_pct": round(caso.retorno * 100, 2),
            "paga_alcabala": caso.paga_alcabala, "casa_habitacion": caso.casa_habitacion,
        },
        "resultado": {
            "efectivo_inicial": round(entrada["total"]),
            "cuota_credito": round(cuota_mensual(caso.precio * (1 - caso.inicial_pct), caso.tea, caso.plazo_anios * 12)),
            "costo_mensual_comprar": round(float(primer["costo_comprar"])),
            "patrimonio_comprar": round(float(final["patrimonio_comprar"])),
            "patrimonio_alquilar": round(float(final["patrimonio_alquilar"])),
            "comprar_gana_desde_anio": None if equilibrio is None else round(equilibrio / 12, 1),
        },
        "empates": {
            "apreciacion_pct": empate("apreciacion", -0.05, 0.15),
            "retorno_pct": empate("retorno", 0.0, 0.30),
            "tea_pct": empate("tea", 0.001, 0.25),
            "alquiler_mensual": None if alquiler_empate is None else round(alquiler_empate),
        },
        "supuestos_mas_sensibles": [
            {"parametro": f["parametro"], "con_valor": f["valor_bajo"], "ventaja": round(f["ventaja_bajo"]),
             "o_con_valor": f["valor_alto"], "o_ventaja": round(f["ventaja_alto"])}
            for f in tornado.to_dict("records")
        ],
        "historia_precios_bcrp": {
            "variacion_nominal_anual_pct": {f"{n}_anios": round(datos.crecimiento_precios(n) * 100, 1) for n in (5, 10, 13)},
            "hasta": datos.bcrp_trimestral()["periodo"].iloc[-1],
        },
        "tasas_bcrp": {"periodo": datos.ultimo("tasa_hipotecaria_mn")[1]},
    }


def distritos(a) -> dict:
    _validar(a)
    tabla = datos.distritos()
    d = analysis.por_distrito(datos.caso(1.0, 1.0, **_cambios(a)), a.anios, tabla, a.m2)
    return {
        "anios": a.anios, "m2": a.m2,
        "distritos": [
            {"distrito": f["distrito"], "precio": round(f["precio"]), "alquiler_mensual": round(f["alquiler"]),
             "rentabilidad_bruta_pct": round(f["rentabilidad"] * 100, 2), "ventaja_comprar": round(f["ventaja"])}
            for f in d.to_dict("records")
        ],
    }


def _opciones_comunes(p):
    for nombre, ayuda in (("--inicial", "cuota inicial, %"), ("--tea", "tasa hipotecaria, %"),
                          ("--apreciacion", "apreciación anual, %"), ("--alza-alquiler", "alza anual del alquiler, %"),
                          ("--retorno", "retorno neto de la inversión, %"), ("--mantenimiento", "mantenimiento anual, %"),
                          ("--costo-venta", "costo de vender, %")):
        p.add_argument(nombre, type=float, help=ayuda)
    p.add_argument("--plazo", type=int, help="plazo del crédito en años")
    p.add_argument("--anios", type=int, default=10, help="años que se quedaría (1 a 30)")
    p.add_argument("--primera-venta", action="store_true", help="compra a constructora: sin alcabala")
    p.add_argument("--no-casa-habitacion", action="store_true", help="no sería su vivienda: paga 5%% de la ganancia")


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Comprar o alquilar en Lima")
    sub = parser.add_subparsers(dest="comando", required=True)
    p = sub.add_parser("analizar", help="un escenario")
    p.add_argument("--distrito")
    p.add_argument("--m2", type=float)
    p.add_argument("--precio", type=float, help="precio de compra en soles")
    p.add_argument("--alquiler", type=float, help="alquiler mensual en soles")
    _opciones_comunes(p)
    p = sub.add_parser("distritos", help="mismos supuestos en todos los distritos")
    p.add_argument("--m2", type=float, required=True)
    _opciones_comunes(p)
    sub.add_parser("app", help="abre la página de Streamlit")
    a = parser.parse_args()

    if a.comando == "app":
        return subprocess.call([sys.executable, "-m", "streamlit", "run", str(RAIZ / "app.py")], cwd=RAIZ)
    try:
        salida = analizar(a) if a.comando == "analizar" else distritos(a)
    except ErrorEntrada as e:
        print(json.dumps({"error": str(e)}, ensure_ascii=False, indent=2))
        return 2
    print(json.dumps(salida, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
