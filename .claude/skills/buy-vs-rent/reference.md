# Referencia del modelo buy-vs-rent

## Método

Simulación mensual a 30 años en soles nominales (`housing_lima/model.py`).

1. **Entrada.** Quien compra paga la cuota inicial, notaría y registros, y alcabala. Quien alquila invierte ese mismo efectivo.
2. **Cada mes.** Comprar cuesta cuota + seguros + predial, arbitrios y mantenimiento. Alquilar cuesta el alquiler, que sube una vez al año. El camino más barato invierte la diferencia, así que ambos gastan lo mismo.
3. **Crédito.** Sistema francés: cuota fija, con tasa mensual `(1 + TEA)^(1/12) - 1`.
4. **Patrimonio de quien compra, si vende en el mes t.** Valor de la vivienda − costo de vender − saldo del crédito − impuesto a la ganancia + su cartera.
5. **Patrimonio de quien alquila.** Su cartera.
6. **Ventaja de comprar.** Patrimonio de quien compra − patrimonio de quien alquila.

`comprar_gana_desde_anio` es el primer momento desde el cual comprar queda por delante hasta el año 30. Si es `null`, no ocurre en 30 años. Un `empate` en `null` significa que no hay cruce dentro del rango evaluado.

## Salida de `hl.py analizar`

| Campo | Significado |
|---|---|
| `veredicto`, `razones` | Frases listas para usar |
| `casi_empate` | La diferencia es menor al 5% del patrimonio |
| `ventaja_comprar` | Positivo: gana comprar. Negativo: gana alquilar. En soles de ese año |
| `origen` | Si el precio y el alquiler son del usuario o estimados |
| `entradas` | Los supuestos que se usaron de verdad |
| `resultado` | Efectivo inicial, cuota, costo mensual y patrimonios |
| `empates` | Valor de cada parámetro en el que ambos caminos empatan |
| `supuestos_mas_sensibles` | Los tres parámetros que más mueven el resultado |
| `historia_precios_bcrp` | Variación nominal anual del precio por m² a 5, 10 y 13 años |

## Datos

| Archivo | Contenido | Fuente |
|---|---|---|
| `data/distritos_urbania.csv` | Precio por m² y alquiler de 100 m² en 15 distritos, mayo de 2025 | Urbania, Index Lima |
| `data/bcrp_mensual.csv` | Tasa hipotecaria, depósitos, tasa de referencia, inflación y tipo de cambio | BCRP |
| `data/bcrp_trimestral.csv` | Precio por m² en 12 distritos, nominal y real | BCRP |
| `config/supuestos.json` | Supuestos con su tipo y fuente, e índice de Urbania para el ajuste | Varias |

Series del BCRP: PN07848NM, PN07815NM, PD04722MM, PN01273PM, PN01210PM, PD37946PQ y PD37945PQ.

Los valores por distrito se llevan a abril de 2026 con un solo factor, la variación del índice de Lima (precio ×1.010, alquiler ×1.046). No recoge lo que cambió en cada distrito. El precio y el alquiler se escalan en proporción al área, aunque los departamentos chicos suelen costar más por m².

## Actualizar los datos

```bash
python scripts/actualizar_bcrp.py
```

Actualiza las series del BCRP; la tasa hipotecaria y el retorno del caso base se leen de ahí. Los datos de Urbania y los valores de `config/supuestos.json` se actualizan a mano. La UIT cambia cada año.

## Lo que el modelo no captura

- **Riesgo:** apreciación y retorno son constantes, y el crédito amplifica las caídas del precio.
- **Precios de aviso:** Urbania mide oferta, no ventas cerradas.
- **Fuera del modelo:** Bono Mivivienda, créditos en dólares, prepagos y garantía del alquiler.
- **Comportamiento:** supone que quien alquila invierte la diferencia todos los meses.
- **Impuestos:** el 5% se aplica sobre la ganancia sin el ajuste por inflación que permite la norma, y se aplica la exoneración por casa-habitación desde los 2 años sin revisar otras condiciones.

## Fuentes

- BCRP: https://estadisticas.bcrp.gob.pe/estadisticas/series/
- Urbania, Index Lima de mayo de 2025: https://urbania.pe/blog/wp-content/uploads/2025/06/INDEX_LIMA_REPORTE_2025-05.pdf
- Índice a abril de 2026, según Infobae: https://www.infobae.com/peru/2026/05/09/este-es-el-nuevo-distrito-mas-caro-para-comprar-un-departamento-supero-a-barranco-con-un-precio-promedio-de-s-9268/
- UIT 2026: https://busquedas.elperuano.pe/dispositivo/NL/2469116-1
- SUNAT, venta de inmuebles: https://personas.sunat.gob.pe/vendo-mi-casa/rentas-segunda-categoria
