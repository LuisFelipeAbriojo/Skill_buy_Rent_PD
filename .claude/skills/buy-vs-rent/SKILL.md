---
name: buy-vs-rent
description: Compara comprar un departamento con alquilar e invertir la diferencia en Lima, Perú, con un modelo mensual y datos del BCRP y Urbania. Úsala siempre que alguien pregunte si le conviene comprar o alquilar vivienda en Lima, evalúe un aviso o un crédito hipotecario frente a seguir alquilando, compare distritos de Lima para comprar, o quiera saber qué apreciación o tasa hace que comprar valga la pena, aunque no diga "comprar vs. alquilar". También sirve para abrir la página de Streamlit del proyecto. No la uses para viviendas fuera de Lima ni para comprar un inmueble solo para alquilarlo a terceros.
---

# Comprar o alquilar en Lima

El modelo responde una pregunta concreta: si dos hogares gastan lo mismo cada mes, ¿quién termina con más patrimonio, el que compra o el que alquila e invierte la diferencia? Haz las cuentas con el script en lugar de estimarlas, porque cuota, impuestos y empates no se pueden calcular de cabeza con precisión.

## Flujo

1. **Reúne lo que falte, sin interrogar.** Necesitas el distrito y el área, o el precio y el alquiler de un aviso. Si faltan datos no críticos, usa el caso base y dilo. Vale la pena preguntar por el horizonte si no se mencionó, porque suele cambiar la respuesta.
2. **Corre el modelo** desde la raíz del proyecto:

   ```bash
   .venv/Scripts/python .claude/skills/buy-vs-rent/scripts/hl.py analizar --distrito "Jesús María" --m2 70 --anios 10
   ```

   Si `.venv` no existe, créalo con los pasos del `README.md`.
3. **Responde con el formato de abajo**, usando las cifras del JSON tal como salen.

## Comandos

| Pregunta | Comando |
|---|---|
| Un distrito | `hl.py analizar --distrito Lince --m2 70 --anios 15` |
| Un aviso real | `hl.py analizar --precio 450000 --alquiler 2300 --anios 10` |
| Solo se conoce el precio | `hl.py analizar --distrito Lince --m2 70 --precio 450000` (el alquiler sale estimado) |
| Comparar distritos | `hl.py distritos --m2 70 --anios 10` |
| Abrir la página | `hl.py app` |

Opciones de `analizar` y `distritos`: `--inicial`, `--tea`, `--plazo`, `--apreciacion`, `--alza-alquiler`, `--retorno`, `--mantenimiento`, `--costo-venta`, `--primera-venta` (compra a constructora: sin alcabala) y `--no-casa-habitacion`.

Los porcentajes se escriben en %: `--tea 7.2` es 7.2%. El monto de la cuota inicial en soles hay que convertirlo primero a porcentaje del precio.

Para el retorno, usa lo que el usuario diga que haría con su dinero. Si no lo dice, el caso base es un depósito a plazo. Para un fondo de renta fija usa `--retorno 5.5` y para un ETF global de bolsa `--retorno 8`, y aclara que esos dos valores son supuestos y que el ETF tiene mucho más riesgo.

## Si algo no calza

- **Distrito sin datos:** el script devuelve un `error` con los 15 distritos disponibles. Pide el precio y el alquiler de un aviso. No uses otro distrito como sustituto sin decirlo, porque el resultado depende de la relación entre precio y alquiler de cada zona.
- **Casa de dos pisos, terreno o local:** los datos son de departamentos. Usa `--precio` y `--alquiler` con datos del usuario y avisa de que los costos son los de un departamento.
- **Crédito en dólares o bono Mivivienda:** están fuera del modelo. Dilo y ofrece, a lo sumo, una aproximación con `--tea` o un precio neto del bono, marcada como aproximación.
- **Compra para alquilar a terceros:** el modelo no sirve, porque no incluye esos ingresos ni sus impuestos.

## Formato de respuesta

Responde en el idioma del usuario y en este orden:

1. **Resultado en una frase**, con `veredicto`. Si `casi_empate` es `true`, dilo en la misma frase: la recomendación honesta ahí es que la decisión depende de otros factores.
2. **De dónde sale**, con dos o tres cifras: efectivo inicial, costo mensual de comprar contra alquiler, y patrimonio final de cada camino.
3. **Qué lo cambiaría:** el empate de apreciación (`empates.apreciacion_pct`) y el supuesto más sensible, comparados con lo que asume el escenario. Para juzgar si la apreciación es razonable, compárala con `historia_precios_bcrp`. Es lo más útil para decidir, porque casi siempre el resultado depende de supuestos inciertos.
4. **Qué es dato y qué es supuesto:** indica si el precio y el alquiler son del usuario o estimados, según `origen`.
5. **Una línea final:** "Es una comparación de escenarios, no asesoría financiera."

Mantén la respuesta corta: cuatro viñetas como máximo, como en el ejemplo. El JSON trae más empates y sensibilidades de los que hacen falta; elige los dos que más ayudan a decidir y ofrece el resto si lo piden, porque una lista larga de condiciones esconde el resultado.

**Ejemplo** (las cifras son ilustrativas; usa siempre las del JSON):

> A 10 años, alquilar e invertir te deja unos S/ 12,000 más, pero es casi un empate.
>
> - Comprar requiere S/ 122,000 de entrada y S/ 3,900 al mes, contra S/ 2,450 de alquiler.
> - Al año 10, quien compra llega a S/ 363,000 y quien alquila, a S/ 375,000.
> - Lo que más lo cambia es la apreciación: el empate está en 2.7% anual y este escenario supone 2.5%. El BCRP registra +0.1% anual en los últimos 5 años y +3.7% en 13.
>
> El precio y el alquiler son estimados para el distrito, no de un aviso real. Es una comparación de escenarios, no asesoría financiera.

## Cuidado al interpretar

- No conviertas una diferencia chica en una recomendación firme. Una diferencia de pocos miles de soles a 10 años no distingue un camino del otro, dados los supuestos.
- `ventaja_comprar` está en soles de ese año; `ventaja_comprar_soles_de_hoy` descuenta inflación. Di cuál estás usando si muestras ambas.
- El modelo no valora la estabilidad de ser dueño, la flexibilidad de alquilar ni el riesgo de que quien alquila no invierta de verdad. Menciónalo si la persona parece decidir solo por el número.

Lee `reference.md` cuando te pregunten cómo funciona el modelo, de dónde salen los datos o cómo actualizarlos.
