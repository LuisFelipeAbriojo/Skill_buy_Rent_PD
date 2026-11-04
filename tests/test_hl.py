import json
import subprocess
import sys
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from housing_lima import datos
from housing_lima.model import simular

RAIZ = Path(__file__).resolve().parents[1]
HL = RAIZ / ".claude" / "skills" / "buy-vs-rent" / "scripts" / "hl.py"


def correr(*args):
    r = subprocess.run([sys.executable, str(HL), *args], capture_output=True, encoding="utf-8", cwd=RAIZ)
    return r.returncode, json.loads(r.stdout)


def test_analizar_coincide_con_el_modelo():
    codigo, s = correr("analizar", "--precio", "450000", "--alquiler", "2300", "--anios", "15", "--tea", "7.2")
    assert codigo == 0
    esperado = simular(datos.caso(450_000, 2_300, tea=0.072)).iloc[180]["ventaja_comprar"]
    assert s["ventaja_comprar"] == round(esperado)
    assert s["origen"]["precio"] == "dato del usuario"


def test_skill_y_pagina_dan_el_mismo_resultado_por_defecto():
    _, s = correr("analizar", "--distrito", "Jesús María", "--m2", "70", "--anios", "10")
    at = AppTest.from_file(str(RAIZ / "app.py"), default_timeout=60).run()
    assert not at.exception
    assert at.title[0].value.replace(" ", " ") == s["veredicto"]


@pytest.mark.parametrize("nombre,esperado", [("surco", "Santiago de Surco"), ("JESUS MARIA", "Jesús María"), ("magdalena", "Magdalena del Mar")])
def test_nombres_flexibles_de_distrito(nombre, esperado):
    _, s = correr("analizar", "--distrito", nombre, "--m2", "70")
    assert s["origen"]["distrito"] == esperado


@pytest.mark.parametrize("args,texto", [
    (["--distrito", "Ate", "--m2", "70"], "sin datos"),
    (["--distrito", "san", "--m2", "70"], "ambiguo"),
    (["--distrito", "Lince"], "--m2"),
    (["--precio", "450000"], "--alquiler"),
    (["--precio", "450000", "--alquiler", "2300", "--anios", "40"], "--anios"),
    (["--precio", "-1", "--alquiler", "2300"], "mayores"),
])
def test_entradas_invalidas_devuelven_error_claro(args, texto):
    codigo, s = correr("analizar", *args)
    assert codigo == 2 and texto in s["error"]


def test_precio_propio_con_alquiler_estimado():
    _, s = correr("analizar", "--distrito", "Lince", "--m2", "70", "--precio", "450000")
    assert s["entradas"]["precio"] == 450_000
    assert s["origen"]["precio"] == "dato del usuario" and s["origen"]["alquiler"].startswith("estimado")


def test_distritos_ordenados_y_completos():
    _, s = correr("distritos", "--m2", "70", "--anios", "10")
    v = [d["ventaja_comprar"] for d in s["distritos"]]
    assert len(v) == 15 and v == sorted(v, reverse=True)
