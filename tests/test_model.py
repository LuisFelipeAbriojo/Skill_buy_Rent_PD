import numpy as np
import pytest

from housing_lima.analysis import mapa_calor, tornado, umbral
from housing_lima.model import Caso, cuota_mensual, efectivo_inicial, mes_equilibrio, simular, tasa_mensual, ventaja

BASE = Caso(precio=500_000, alquiler=2_400)


def test_tasa_mensual_compone_a_la_tea():
    assert (1 + tasa_mensual(0.0747)) ** 12 - 1 == pytest.approx(0.0747)


def test_cuota_contra_calculo_a_mano():
    # 400 mil a 12% TEA y 20 años: i = 0,94888% mensual, (1+i)^-240 = 1,12^-20 = 0,10367
    # cuota = 400000 * 0,0094888 / 0,89633 = 4234,5
    assert cuota_mensual(400_000, 0.12, 240) == pytest.approx(4_234.5, abs=1)


def test_saldo_termina_en_cero_y_coincide_con_amortizar_mes_a_mes():
    sim = simular(BASE)
    i = tasa_mensual(BASE.tea)
    saldo = 400_000.0
    for m in range(1, 241):
        saldo = saldo * (1 + i) - sim["cuota"].iloc[m]
        assert sim["saldo"].iloc[m] == pytest.approx(saldo, abs=1e-5)
    assert sim["saldo"].iloc[240] == pytest.approx(0, abs=1e-5)
    assert sim["cuota"].iloc[241] == 0


def test_alcabala_solo_sobre_el_exceso_de_10_uit():
    assert efectivo_inicial(BASE)["alcabala"] == pytest.approx(0.03 * (500_000 - 55_000))
    assert efectivo_inicial(BASE.con(paga_alcabala=False))["alcabala"] == 0
    assert efectivo_inicial(BASE.con(precio=50_000))["alcabala"] == 0


def test_alquiler_sube_una_vez_al_anio():
    s = simular(BASE)["costo_alquilar"]
    assert s.iloc[1] == s.iloc[12] == 2_400
    assert s.iloc[13] == pytest.approx(2_400 * 1.03)


def test_mismo_gasto_total_en_ambos_hogares():
    """Gasto + aporte a la cartera debe ser igual cada mes: es la base de la comparación."""
    sim = simular(BASE)
    r = tasa_mensual(BASE.retorno)
    aporte_inq = sim["cartera_inquilino"].diff() - sim["cartera_inquilino"].shift() * r
    aporte_com = sim["cartera_comprador"].diff() - sim["cartera_comprador"].shift() * r
    izq = (sim["costo_comprar"] + aporte_com).iloc[1:]
    der = (sim["costo_alquilar"] + aporte_inq).iloc[1:]
    assert np.allclose(izq, der, atol=1e-6)


def test_patrimonio_cuadra_con_sus_componentes():
    f = simular(BASE).iloc[120]
    assert f["patrimonio_comprar"] == pytest.approx(
        f["valor"] - f["costo_vender"] - f["saldo"] - f["impuesto"] + f["cartera_comprador"])


def test_casa_habitacion_exonera_solo_desde_dos_anios():
    alta = BASE.con(apreciacion=0.10)
    sim = simular(alta)
    assert sim["impuesto"].iloc[23] > 0 and sim["impuesto"].iloc[24] == 0
    assert simular(alta.con(casa_habitacion=False))["impuesto"].iloc[24] > 0


@pytest.mark.parametrize("campo,cambio,signo", [
    ("apreciacion", 0.01, 1), ("alquiler", 300, 1), ("alza_alquiler", 0.01, 1),
    ("tea", 0.01, -1), ("retorno", 0.01, -1), ("precio", 50_000, -1),
])
def test_cada_parametro_mueve_la_ventaja_en_el_sentido_correcto(campo, cambio, signo):
    alto = BASE.con(**{campo: getattr(BASE, campo) + cambio})
    assert (ventaja(alto, 15) - ventaja(BASE, 15)) * signo > 0


def test_umbral_da_empate():
    a = umbral(BASE, 15, "apreciacion", -0.05, 0.15)
    assert ventaja(BASE.con(apreciacion=a), 15) == pytest.approx(0, abs=1)


def test_umbral_sin_cruce_devuelve_none():
    assert umbral(BASE, 15, "apreciacion", 0.20, 0.30) is None


def test_mes_equilibrio_coincide_con_la_serie():
    sim = simular(BASE.con(apreciacion=0.05))
    m = mes_equilibrio(sim)
    assert m is not None and (sim["ventaja_comprar"].iloc[m:] >= 0).all() and sim["ventaja_comprar"].iloc[m - 1] < 0


def test_mes_equilibrio_nunca():
    assert mes_equilibrio(simular(BASE.con(apreciacion=-0.05, retorno=0.15))) is None


def test_tornado_y_mapa_tienen_la_forma_esperada():
    assert tornado(BASE, 10)["rango"].is_monotonic_decreasing
    assert mapa_calor(BASE, 10).shape == (9, 7)
