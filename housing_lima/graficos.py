"""Gráficos Plotly de la página. Azul es comprar y naranja, alquilar, en todas las vistas."""
import plotly.graph_objects as go

AZUL = "#2a78d6"
NARANJA = "#eb6834"
AQUA = "#1baf7a"
TINTA = "#0b0b0b"
TINTA_2 = "#52514e"
TENUE = "#898781"
GRILLA = "#e1e0d9"
BASE = "#c3c2b7"
DIVERGENTE = [[0, "#b52f2f"], [0.25, "#e88a89"], [0.5, "#f0efec"], [0.75, "#86b6ef"], [1, "#184f95"]]
FUENTE = 'system-ui, -apple-system, "Segoe UI", sans-serif'
MILES = dict(separatethousands=True)


def _estilo(fig, alto, margen=None, leyenda=True):
    fig.update_layout(
        height=alto, margin=margen or dict(l=8, r=8, t=36, b=8),
        font=dict(family=FUENTE, size=13, color=TINTA_2),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        showlegend=leyenda,
        legend=dict(orientation="h", y=1.02, yanchor="bottom", x=0, xanchor="left", title_text=""),
        hoverlabel=dict(bgcolor="#fcfcfb", bordercolor=GRILLA, font=dict(family=FUENTE, color=TINTA, size=13)),
    )
    fig.update_xaxes(gridcolor=GRILLA, linecolor=BASE, zeroline=False, tickfont=dict(color=TENUE),
                     automargin=True, title_standoff=12)
    fig.update_yaxes(gridcolor=GRILLA, linecolor=BASE, zeroline=False, tickfont=dict(color=TENUE),
                     automargin=True, title_standoff=12)
    return fig


def _rotulos_finales(fig, d, a, b):
    """Rotula el final de dos líneas; la de arriba sube y la de abajo baja para que no se pisen."""
    x = d["anio"].iloc[-1]
    (col_a, texto_a), (col_b, texto_b) = a, b
    a_arriba = d[col_a].iloc[-1] >= d[col_b].iloc[-1]
    for col, texto, sube in ((col_a, texto_a, a_arriba), (col_b, texto_b, not a_arriba)):
        fig.add_annotation(x=x, y=d[col].iloc[-1], text=texto, xanchor="left", xshift=8,
                           yshift=8 if sube else -8, showarrow=False, font=dict(color=TINTA_2, size=13))


def patrimonio(sim, anios, equilibrio):
    d = sim.iloc[: anios * 12 + 1]
    fig = go.Figure()
    for col, nombre, color in (("patrimonio_comprar", "Comprar", AZUL),
                               ("patrimonio_alquilar", "Alquilar e invertir", NARANJA)):
        fig.add_scatter(x=d["anio"], y=d[col], name=nombre, mode="lines", line=dict(color=color, width=2),
                        hovertemplate="%{y:,.0f}<extra>" + nombre + "</extra>")
    _rotulos_finales(fig, d, ("patrimonio_comprar", "Comprar"), ("patrimonio_alquilar", "Alquilar"))
    if equilibrio is not None and 0 < equilibrio <= anios * 12:
        fig.add_vline(x=equilibrio / 12, line=dict(color=TENUE, width=1, dash="dot"))
        fig.add_annotation(x=equilibrio / 12, y=1, yref="paper", text="Empate", showarrow=False,
                           yanchor="bottom", font=dict(color=TINTA_2, size=12))
    _estilo(fig, 380, dict(l=8, r=78, t=44, b=8))
    fig.update_layout(hovermode="x unified")
    fig.update_xaxes(title_text="Años desde la compra", dtick=5 if anios > 10 else 1,
                     hoverformat=".1f", showgrid=False)
    fig.update_xaxes(range=[0, anios])
    fig.update_yaxes(title_text="Patrimonio si se vende ese año (S/)", rangemode="tozero", tickformat=",.0f")
    return fig


def flujo_mensual(sim, anios):
    d = sim.iloc[1: anios * 12 + 1]
    fig = go.Figure()
    for col, nombre, color in (("costo_comprar", "Comprar", AZUL), ("costo_alquilar", "Alquilar", NARANJA)):
        fig.add_scatter(x=d["anio"], y=d[col], name=nombre, mode="lines", line=dict(color=color, width=2),
                        hovertemplate="%{y:,.0f}<extra>" + nombre + "</extra>")
    _rotulos_finales(fig, d, ("costo_comprar", "Comprar"), ("costo_alquilar", "Alquilar"))
    _estilo(fig, 300, dict(l=8, r=78, t=44, b=8))
    fig.update_layout(hovermode="x unified")
    fig.update_xaxes(title_text="Años desde la compra", dtick=5 if anios > 10 else 1,
                     hoverformat=".1f", showgrid=False)
    fig.update_xaxes(range=[0, anios])
    fig.update_yaxes(title_text="Salida mensual (S/)", rangemode="tozero", tickformat=",.0f")
    return fig


def tornado(t, base):
    t = t.iloc[::-1]
    fig = go.Figure()
    for col, nombre, color, etiqueta in (("ventaja_bajo", "Valor bajo", "#86b6ef", "valor_bajo"),
                                         ("ventaja_alto", "Valor alto", "#184f95", "valor_alto")):
        fig.add_bar(y=t["parametro"], x=t[col] - base, base=base, name=nombre, orientation="h",
                    marker=dict(color=color, cornerradius=4), customdata=t[[etiqueta, col]],
                    hovertemplate="%{y}: %{customdata[0]}<br>Ventaja de comprar: S/ %{customdata[1]:,.0f}<extra></extra>")
    fig.add_vline(x=0, line=dict(color=TINTA_2, width=1))
    fig.add_annotation(x=0, y=1, yref="paper", text="Empate", showarrow=False, yanchor="bottom",
                       font=dict(color=TINTA_2, size=12))
    _estilo(fig, 400, dict(l=8, r=16, t=48, b=8))
    fig.update_layout(barmode="overlay", bargap=0.45)
    fig.update_xaxes(title_text="Ventaja de comprar (S/): a la derecha conviene comprar", tickformat=",.0f")
    fig.update_yaxes(showgrid=False)
    return fig


def mapa_calor(m, apreciacion, retorno):
    z = m.to_numpy() / 1000
    tope = max(abs(z.min()), abs(z.max()))
    fig = go.Figure(go.Heatmap(
        z=z, x=[c * 100 for c in m.columns], y=[r * 100 for r in m.index],
        colorscale=DIVERGENTE, zmid=0, zmin=-tope, zmax=tope, xgap=2, ygap=2,
        text=[[f"{v:,.0f}" for v in fila] for fila in z], texttemplate="%{text}",
        colorbar=dict(title=dict(text="S/ miles", side="top"), thickness=10, outlinewidth=0,
                      tickfont=dict(color=TENUE)),
        hovertemplate="Apreciación %{x:.0f}% · Retorno %{y:.0f}%<br>Ventaja de comprar: S/ %{z:,.0f} mil<extra></extra>",
    ))
    fig.add_scatter(x=[apreciacion * 100], y=[retorno * 100], mode="markers", name="Tu escenario",
                    marker=dict(size=14, color="rgba(0,0,0,0)", line=dict(color=TINTA, width=2)),
                    hovertemplate="Tu escenario<extra></extra>")
    _estilo(fig, 440, dict(l=8, r=8, t=40, b=8))
    fig.update_xaxes(title_text="Apreciación anual de la vivienda (%)", dtick=1, showgrid=False)
    fig.update_yaxes(title_text="Retorno anual de la inversión (%)", dtick=1, showgrid=False)
    return fig


def distritos(d, seleccionado, anios):
    d = d.iloc[::-1]
    etiquetas = [f"<b>{n}</b>" if n == seleccionado else n for n in d["distrito"]]
    fig = go.Figure()
    for nombre, color, filtro in (("Conviene comprar", AZUL, d["ventaja"] >= 0),
                                  ("Conviene alquilar", NARANJA, d["ventaja"] < 0)):
        fig.add_bar(y=[e for e, f in zip(etiquetas, filtro) if f], x=d.loc[filtro, "ventaja"], name=nombre,
                    orientation="h", marker=dict(color=color, cornerradius=4),
                    customdata=d.loc[filtro, ["precio", "alquiler"]],
                    hovertemplate="%{y}<br>Ventaja de comprar: S/ %{x:,.0f}<br>Precio: S/ %{customdata[0]:,.0f}"
                                  "<br>Alquiler: S/ %{customdata[1]:,.0f}<extra></extra>")
    fig.add_vline(x=0, line=dict(color=BASE, width=1))
    _estilo(fig, 500, dict(l=8, r=16, t=44, b=8))
    fig.update_layout(bargap=0.3)
    fig.update_xaxes(title_text=f"Ventaja de comprar a {anios} años (S/)", tickformat=",.0f")
    fig.update_yaxes(categoryorder="array", categoryarray=etiquetas, showgrid=False)
    return fig


def precios_historicos(d):
    fig = go.Figure()
    for col, nombre, color in (("precio_m2_corriente", "S/ corrientes", AZUL),
                               ("precio_m2_constante", "S/ constantes de 2009", AQUA)):
        fig.add_scatter(x=d["fecha"], y=d[col], name=nombre, mode="lines", line=dict(color=color, width=2),
                        hovertemplate="S/ %{y:,.0f}<extra>" + nombre + "</extra>")
    _estilo(fig, 320)
    fig.update_layout(hovermode="x unified")
    fig.update_xaxes(showgrid=False, hoverformat="%Y")
    fig.update_yaxes(title_text="Precio por m² (S/)", rangemode="tozero", tickformat=",.0f")
    return fig


def tasas_historicas(d):
    fig = go.Figure()
    for col, nombre, color in (("tasa_hipotecaria_mn", "Hipotecaria", AZUL),
                               ("tasa_deposito_360_mn", "Depósito a 360 días o más", AQUA),
                               ("tasa_referencia", "Tasa de referencia", "#eda100")):
        s = d.dropna(subset=[col])
        fig.add_scatter(x=s["fecha"], y=s[col], name=nombre, mode="lines", line=dict(color=color, width=2),
                        hovertemplate="%{y:.2f}%<extra>" + nombre + "</extra>")
    _estilo(fig, 320)
    fig.update_layout(hovermode="x unified")
    fig.update_xaxes(showgrid=False, hoverformat="%b %Y")
    fig.update_yaxes(title_text="Tasa anual en soles (%)", rangemode="tozero")
    return fig
