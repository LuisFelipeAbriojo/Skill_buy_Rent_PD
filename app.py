"""Comprar o alquilar en Lima. Ejecutar con: streamlit run app.py"""
import pandas as pd
import streamlit as st

from housing_lima import analysis, datos, explain, graficos
from housing_lima.explain import pct, soles
from housing_lima.model import Caso, cuota_mensual, efectivo_inicial, mes_equilibrio, simular

st.set_page_config(page_title="Comprar o alquilar en Lima", page_icon="🏠", layout="wide")
st.markdown("<style>[data-testid='stMetricValue']{font-size:1.6rem}</style>", unsafe_allow_html=True)

cfg = datos.config()
S = {k: v["valor"] for k, v in cfg["supuestos"].items()}
tabla_distritos = datos.distritos()
tea_bcrp, periodo_tea = datos.ultimo("tasa_hipotecaria_mn")
dep_bcrp, periodo_dep = datos.ultimo("tasa_deposito_360_mn")
PERSONALIZADO = "Personalizado"


def grafico(fig):
    st.plotly_chart(fig, width="stretch", theme=None, config={"displayModeBar": False})


# ---------- Controles ----------
with st.sidebar:
    st.header("Tu escenario")

    st.subheader("Vivienda")
    nombres = tabla_distritos["distrito"].tolist()
    distrito = st.selectbox("Distrito", nombres, index=nombres.index("Jesús María"))
    m2 = st.slider("Área (m²)", 40, 200, 70, step=5)
    fila = tabla_distritos.set_index("distrito").loc[distrito]
    precio_ref, alquiler_ref = float(fila["precio_m2"] * m2), float(fila["alquiler_100m2"] * m2 / 100)
    if st.toggle("Usar un aviso real", help="Reemplaza las referencias del distrito por el precio y el alquiler de un aviso."):
        precio = st.number_input("Precio de compra (S/)", 50_000, 5_000_000, int(round(precio_ref, -3)), step=5_000)
        alquiler = st.number_input("Alquiler equivalente (S/ al mes)", 300, 30_000, int(round(alquiler_ref, -1)), step=50)
    else:
        precio, alquiler = precio_ref, alquiler_ref
        st.caption(f"Referencia del distrito: precio **{soles(precio)}**, alquiler **{soles(alquiler)}** al mes.")

    st.subheader("Crédito")
    inicial = st.slider("Cuota inicial (%)", 10, 50, round(S["inicial_pct"] * 100), step=5) / 100
    tea = st.slider("Tasa hipotecaria, TEA (%)", 5.0, 12.0, round(tea_bcrp, 1), step=0.1,
                    help=f"Promedio de bancos en soles según el BCRP: {tea_bcrp:.2f}% a {periodo_tea}.") / 100
    plazo = st.slider("Plazo (años)", 10, 30, S["plazo_anios"], step=5)

    st.subheader("Hacia adelante")
    anios = st.slider("¿Cuántos años te quedarías?", 1, 30, 10)
    apreciacion = st.slider("Apreciación anual de la vivienda (%)", -2.0, 8.0, S["apreciacion"] * 100, step=0.5) / 100
    alza = st.slider("Alza anual del alquiler (%)", 0.0, 8.0, S["alza_alquiler"] * 100, step=0.5) / 100

    alternativas = {k: {**v} for k, v in cfg["alternativas"].items()}
    primera = next(iter(alternativas))
    alternativas[primera]["valor"] = dep_bcrp / 100
    opcion = st.selectbox("Si no compras, ¿dónde inviertes?", [*alternativas, PERSONALIZADO])
    if opcion == PERSONALIZADO:
        retorno = st.slider("Retorno neto anual (%)", 0.0, 15.0, 6.0, step=0.5) / 100
    else:
        retorno = alternativas[opcion]["valor"]
        st.caption(f"Retorno: **{pct(retorno)}** ({alternativas[opcion]['tipo']}). "
                   f"Riesgo: {alternativas[opcion]['riesgo']}")

    with st.expander("Costos e impuestos"):
        casa_habitacion = st.checkbox("Sería tu casa-habitación", True,
                                      help="Con al menos 2 años, la venta queda exonerada del 5% sobre la ganancia.")
        paga_alcabala = st.checkbox("Paga alcabala (vivienda de segunda mano)", True,
                                    help="La primera venta de una constructora no paga alcabala, pero el IGV ya está en su precio.")
        mantenimiento = st.slider("Mantenimiento mayor (% anual)", 0.0, 2.0, S["mantenimiento"] * 100, step=0.1) / 100
        costo_venta = st.slider("Costo de vender (%)", 0.0, 6.0, S["costo_venta"] * 100, step=0.5) / 100

caso = Caso(
    precio=float(precio), alquiler=float(alquiler), inicial_pct=inicial, plazo_anios=plazo, tea=tea,
    apreciacion=apreciacion, alza_alquiler=alza, retorno=retorno, inflacion=S["inflacion"],
    gastos_cierre=S["gastos_cierre"], alcabala=S["alcabala"], uit=S["uit"], paga_alcabala=paga_alcabala,
    predial_arbitrios=S["predial_arbitrios"], mantenimiento=mantenimiento,
    seguro_desgravamen=S["seguro_desgravamen"], seguro_inmueble=S["seguro_inmueble"],
    costo_venta=costo_venta, impuesto_ganancia=S["impuesto_ganancia"], casa_habitacion=casa_habitacion,
)
sim = simular(caso)
final = sim.iloc[anios * 12]
primer_mes = sim.iloc[1]
entrada = efectivo_inicial(caso)
ventaja = float(final["ventaja_comprar"])
equilibrio = mes_equilibrio(sim)

# ---------- Respuesta ----------
st.caption(f"Comprar o alquilar en Lima · {distrito}, {m2} m²")
st.title(explain.veredicto(sim, anios))
hoy = ventaja / (1 + caso.inflacion) ** anios
nota = f"Son {soles(round(abs(hoy), -3))} en soles de hoy, con inflación de {pct(caso.inflacion)}."
if explain.casi_empate(sim, anios):
    nota += " **Es casi un empate:** la diferencia es menor al 5% del patrimonio, así que un supuesto algo distinto puede invertirla."
st.markdown(nota)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Efectivo inicial", soles(entrada["total"]), help="Cuota inicial, notaría y registros, y alcabala.")
c2.metric("Comprar, al mes", soles(primer_mes["costo_comprar"]),
          help=f"Cuota de {soles(primer_mes['cuota'])}, más seguros, predial, arbitrios y mantenimiento.")
c3.metric("Alquilar, al mes", soles(primer_mes["costo_alquilar"]), help="Primer año.")
c4.metric("Comprar gana desde", explain.equilibrio_texto(sim),
          help="Primer momento desde el cual comprar queda por delante hasta el año 30.")

res, sen, dis, dat = st.tabs(["Resultado", "¿Qué lo cambiaría?", "Distritos", "Datos y método"])

# ---------- Resultado ----------
with res:
    izq, der = st.columns([3, 2], gap="large")
    with izq:
        st.subheader("Patrimonio de cada camino")
        grafico(graficos.patrimonio(sim, anios, equilibrio))
    with der:
        st.subheader("Por qué sale así")
        for r in explain.razones(caso, sim, anios):
            st.markdown(r)
        st.info("Ambos caminos gastan lo mismo cada mes. Quien tiene la salida más barata invierte la diferencia.")

    izq, der = st.columns([3, 2], gap="large")
    with izq:
        st.subheader("Salida mensual")
        grafico(graficos.flujo_mensual(sim, anios))
    with der:
        st.subheader(f"Cuentas al año {anios}")
        st.dataframe(pd.DataFrame([
            ("Valor de la vivienda", soles(final["valor"]), "—"),
            ("Costo de vender", soles(-final["costo_vender"]), "—"),
            ("Saldo del crédito", soles(-final["saldo"]), "—"),
            ("Impuesto a la ganancia", soles(-final["impuesto"]), "—"),
            ("Cartera de inversión", soles(final["cartera_comprador"]), soles(final["cartera_inquilino"])),
            ("Patrimonio final", soles(final["patrimonio_comprar"]), soles(final["patrimonio_alquilar"])),
        ], columns=["Concepto", "Comprar", "Alquilar"]), hide_index=True, width="stretch")
        anio1 = sim.iloc[1:13]
        costo_oportunidad = entrada["total"] * caso.retorno
        apreciacion_1 = sim["valor"].iloc[12] - caso.precio
        no_recuperable = anio1["interes"].sum() + anio1["seguros"].sum() + anio1["tenencia"].sum() + costo_oportunidad
        st.markdown(
            f"**En el primer año**, comprar tiene {soles(no_recuperable)} de costo que no se recupera "
            f"(intereses, seguros, gastos y lo que dejó de rendir la entrada), y la vivienda sube {soles(apreciacion_1)}. "
            f"Alquilar cuesta {soles(anio1['costo_alquilar'].sum())}."
        )

# ---------- Sensibilidad ----------
with sen:
    st.subheader("Qué supuesto mueve más la decisión")
    st.caption(f"Cambia un parámetro a la vez, a {explain.anios_texto(anios)}. Cada barra parte de tu escenario.")
    t = analysis.tornado(caso, anios)
    grafico(graficos.tornado(t, ventaja))
    with st.expander("Ver la tabla"):
        st.dataframe(t.assign(
            ventaja_bajo=t["ventaja_bajo"].map(soles), ventaja_alto=t["ventaja_alto"].map(soles),
        )[["parametro", "valor_bajo", "ventaja_bajo", "valor_alto", "ventaja_alto"]].rename(columns={
            "parametro": "Parámetro", "valor_bajo": "Valor bajo", "ventaja_bajo": "Ventaja con valor bajo",
            "valor_alto": "Valor alto", "ventaja_alto": "Ventaja con valor alto",
        }), hide_index=True, width="stretch")

    st.subheader("Apreciación contra retorno de la inversión")
    st.caption("Ventaja de comprar, en miles de soles. Azul: conviene comprar. Rojo: conviene alquilar.")
    grafico(graficos.mapa_calor(analysis.mapa_calor(caso, anios), apreciacion, retorno))

    u_tea = analysis.umbral(caso, anios, "tea", 0.001, 0.25)
    u_ret = analysis.umbral(caso, anios, "retorno", 0.0, 0.30)
    u_alq = analysis.umbral(caso, anios, "alquiler", caso.alquiler * 0.2, caso.alquiler * 4)
    st.subheader("Valores de empate")
    a, b, c = st.columns(3)
    a.metric("Tasa hipotecaria", pct(u_tea) if u_tea is not None else "Sin empate", help=f"Tu escenario: {pct(tea, 2)}")
    b.metric("Retorno de la inversión", pct(u_ret) if u_ret is not None else "Sin empate", help=f"Tu escenario: {pct(retorno, 2)}")
    c.metric("Alquiler mensual", soles(u_alq) if u_alq is not None else "Sin empate", help=f"Tu escenario: {soles(alquiler)}")

# ---------- Distritos ----------
with dis:
    st.subheader(f"Los mismos {m2} m² y supuestos en cada distrito")
    d = analysis.por_distrito(caso, anios, tabla_distritos, m2)
    n_compra = int((d["ventaja"] >= 0).sum())
    st.caption(f"Comprar gana en {n_compra} de {len(d)} distritos a {explain.anios_texto(anios)}. "
               "Pesa la rentabilidad bruta (alquiler anual ÷ precio): a mayor rentabilidad, más conviene comprar.")
    grafico(graficos.distritos(d, distrito, anios))
    st.dataframe(pd.DataFrame({
        "Distrito": d["distrito"],
        "Precio por m²": d["precio_m2"].map(soles),
        "Precio": d["precio"].map(soles),
        "Alquiler mensual": d["alquiler"].map(soles),
        "Rentabilidad bruta": d["rentabilidad"].map(pct),
        "Ventaja de comprar": d["ventaja"].map(soles),
    }), hide_index=True, width="stretch")
    st.caption("Valores estimados: precio y alquiler proporcionales al área. Comparan distritos, no reemplazan un aviso real.")

# ---------- Datos y método ----------
with dat:
    q = datos.bcrp_trimestral()
    m = datos.bcrp_mensual()
    inflacion, periodo_inf = datos.ultimo("inflacion_12m")
    tc, periodo_tc = datos.ultimo("tipo_cambio")
    izq, der = st.columns(2, gap="large")
    with izq:
        st.subheader("El precio real por m² lleva años cayendo")
        grafico(graficos.precios_historicos(q))
        st.caption(
            f"Variación nominal anual: {pct(datos.crecimiento_precios(5), 1)} en 5 años, "
            f"{pct(datos.crecimiento_precios(10), 1)} en 10 y {pct(datos.crecimiento_precios(13), 1)} en 13. "
            f"Real a 5 años: {pct(datos.crecimiento_precios(5, 'precio_m2_constante'), 1)}. "
            f"12 distritos de Lima, BCRP, hasta {q['periodo'].iloc[-1]}."
        )
    with der:
        st.subheader("Tasas en soles")
        grafico(graficos.tasas_historicas(m))
        st.caption(
            f"Inflación en 12 meses: {inflacion:.2f}% a {periodo_inf}"
            f"{', por encima del rango meta de 1% a 3%' if inflacion > 3 else ''}. "
            f"Tipo de cambio: S/ {tc:.2f} a {periodo_tc}. Fuente: BCRP."
        )

    st.subheader("Supuestos del caso base")
    filas = [(v["nombre"], v["tipo"], v["fuente"]) for v in cfg["supuestos"].values()]
    st.table(pd.DataFrame(filas, columns=["Parámetro", "Tipo", "Fuente o razón"]).set_index("Parámetro"))

    st.subheader("Cómo funciona")
    idx = cfg["indice_urbania"]
    st.markdown(f"""
- **Comparación:** simulación mensual a 30 años en soles nominales. Ambos caminos gastan lo mismo, y el resultado es el patrimonio de cada uno si se vende la vivienda ese año.
- **Crédito:** cuota fija (sistema francés) con TEA convertida a tasa mensual. Si vendes antes del final, cancelas el saldo.
- **Precios por distrito:** Urbania Index, {idx['base']['mes']}, llevados a {idx['actual']['mes']} con la variación del índice de Lima (precio ×{idx['actual']['precio_m2'] / idx['base']['precio_m2']:.3f}, alquiler ×{idx['actual']['alquiler_100m2'] / idx['base']['alquiler_100m2']:.3f}). Es un ajuste parejo: no recoge lo que cambió en cada distrito. La rentabilidad se calcula como alquiler anual ÷ precio y puede diferir algo de la que publica Urbania.
""")
    st.subheader("Lo que el modelo no captura")
    st.markdown("""
- **Riesgo:** apreciación y retornos son constantes; en la realidad varían y el crédito amplifica las caídas del precio.
- **Precios de aviso:** Urbania mide oferta, no transacciones cerradas.
- **Estabilidad y uso:** no valora mudarse menos, poder remodelar ni la flexibilidad de alquilar.
- **Disciplina:** supone que quien alquila invierte de verdad la diferencia todos los meses.
- **Fuera del modelo:** Bono Mivivienda y otros subsidios, créditos en dólares, prepagos y garantía del alquiler.
- **Este resultado no es asesoría financiera:** es un ejercicio académico para comparar escenarios.
""")
    st.subheader("Fuentes")
    st.markdown("""
- [BCRP, estadísticas](https://estadisticas.bcrp.gob.pe/estadisticas/series/): precios por m² (PD37945PQ, PD37946PQ), tasas (PN07848NM, PN07815NM, PD04722MM), inflación (PN01273PM) y tipo de cambio (PN01210PM).
- [Urbania, Index Lima de mayo de 2025](https://urbania.pe/blog/wp-content/uploads/2025/06/INDEX_LIMA_REPORTE_2025-05.pdf): precio y alquiler por distrito.
- [Infobae, 9 de mayo de 2026](https://www.infobae.com/peru/2026/05/09/este-es-el-nuevo-distrito-mas-caro-para-comprar-un-departamento-supero-a-barranco-con-un-precio-promedio-de-s-9268/): índice de Lima a abril de 2026.
- [El Peruano, UIT 2026](https://busquedas.elperuano.pe/dispositivo/NL/2469116-1) y [SUNAT, venta de inmuebles](https://personas.sunat.gob.pe/vendo-mi-casa/rentas-segunda-categoria).
""")
