# Comprar o alquilar en Lima

Página de Streamlit que compara comprar un departamento en Lima con alquilar e invertir la diferencia. Usa datos del BCRP y de Urbania guardados en `data/`, así que funciona sin internet.

## Ejecutar

```bash
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt
.venv/Scripts/python -m streamlit run app.py
```

## Probar y actualizar datos

```bash
.venv/Scripts/python -m pytest
python scripts/actualizar_bcrp.py
```

## Estructura

| Ruta | Contenido |
|---|---|
| `app.py` | La página |
| `housing_lima/model.py` | Simulación mensual |
| `housing_lima/analysis.py` | Sensibilidad, empates y distritos |
| `housing_lima/explain.py` | Frases del resultado |
| `housing_lima/graficos.py` | Gráficos |
| `housing_lima/datos.py` | Carga de datos |
| `config/supuestos.json` | Supuestos con su fuente |
| `data/` | Series del BCRP y distritos de Urbania |

El método, los límites y las fuentes están en la pestaña **Datos y método** de la página. Es un ejercicio académico, no asesoría financiera.
