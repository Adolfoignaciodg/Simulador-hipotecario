import streamlit as st
import pandas as pd
import numpy as np
import requests
import plotly.graph_objects as go

# --- Estilos CSS para look premium ---
st.markdown("""
<style>
/* Fuente elegante */
body, .css-1d391kg, .stTextInput, .stNumberInput, .stButton>button {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

/* Fondo blanco con sombra para contenedores */
.css-1y4p8pa {
    background-color: #f9fafb;
    border-radius: 10px;
    padding: 20px;
    box-shadow: 0 3px 10px rgb(0 0 0 / 0.1);
}

/* Botón personalizado */
.stButton>button {
    background-color: #1f77b4;
    color: white;
    font-weight: 600;
    border-radius: 6px;
    padding: 10px 24px;
    transition: background-color 0.3s ease;
}
.stButton>button:hover {
    background-color: #145a86;
}

/* Título principal */
h1 {
    color: #0f3057;
    font-weight: 700;
    font-size: 3rem;
    text-align: center;
    margin-bottom: 20px;
}

/* KPIs estilo tarjeta */
.kpi {
    background-color: white;
    border-radius: 8px;
    padding: 20px;
    text-align: center;
    box-shadow: 0 3px 6px rgb(0 0 0 / 0.1);
    margin: 10px;
}
.kpi h3 {
    margin: 0;
    color: #0f3057;
}
.kpi span {
    font-size: 1.5rem;
    font-weight: 700;
    color: #2a9d8f;
}
</style>
""", unsafe_allow_html=True)

# --- Configuración de página ---
st.set_page_config(page_title="🏡 Simulador Hipotecario Avanzado by Adolf", layout="wide")

# --- Título ---
st.markdown("<h1>🏡 Simulador Hipotecario Avanzado by Adolf</h1>", unsafe_allow_html=True)

# --- Sidebar para inputs ---
st.sidebar.header("Parámetros del Crédito")

precio_uf = st.sidebar.number_input("Precio vivienda (UF)", min_value=1.0, value=4000.0, step=1.0)
pie_uf = st.sidebar.number_input("Pie inicial (UF)", min_value=precio_uf*0.1, max_value=precio_uf, value=precio_uf*0.2, step=1.0)
plazo = st.sidebar.slider("Plazo crédito (años)", min_value=1, max_value=30, value=20)
tasa_anual = st.sidebar.number_input("Tasa interés anual (%)", min_value=0.1, max_value=15.0, value=4.0, step=0.01)
seguro_mensual = st.sidebar.number_input("Seguro mensual (CLP)", min_value=0, value=10000, step=1000)

prepago = st.sidebar.checkbox("Simular prepago parcial")
prepago_monto = 0.0
prepago_ano = 0
if prepago:
    prepago_monto = st.sidebar.number_input("Monto prepago (UF)", min_value=0.0, value=0.0)
    prepago_ano = st.sidebar.number_input("Año prepago", min_value=1, max_value=plazo, value=5)

# --- Llamada a mindicador ---
try:
    data = requests.get("https://mindicador.cl/api").json()
    uf_clp = data["uf"]["valor"]
except:
    uf_clp = 36000

# --- Calcular crédito ---
credito_uf = max(precio_uf - pie_uf, 0)
tasa_mensual = (1 + tasa_anual/100)**(1/12) - 1
n_meses = plazo * 12
dividendo_uf = credito_uf * tasa_mensual / (1 - (1 + tasa_mensual)**-n_meses) if credito_uf > 0 else 0
dividendo_clp = dividendo_uf * uf_clp + seguro_mensual

# --- Botón calcular ---
if st.sidebar.button("🔄 Calcular Crédito"):
    saldo = credito_uf
    interes_total = capital_total = 0
    anios_data = {}
    tabla = []
    anio_salto = None
    for mes in range(1, n_meses + 1):
        interes = saldo * tasa_mensual
        capital = dividendo_uf - interes
        if prepago and mes == prepago_ano * 12:
            saldo -= prepago_monto
        saldo -= capital
        interes_total += interes
        capital_total += capital
        anio = (mes - 1) // 12 + 1
        anios_data.setdefault(anio, {"int": 0, "cap": 0})
        anios_data[anio]["int"] += interes
        anios_data[anio]["cap"] += capital
        tabla.append([mes, anio, capital, interes, saldo])
        if not anio_salto and capital > interes:
            anio_salto = anio

    # --- Mostrar resultados ---
    st.markdown("## Resultados del Crédito")

    # Tarjetas KPI
    kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
    kpi_col1.markdown(f'<div class="kpi"><h3>Monto Crédito</h3><span>{credito_uf:.2f} UF</span></div>', unsafe_allow_html=True)
    kpi_col2.markdown(f'<div class="kpi"><h3>Dividendo Mensual</h3><span>{dividendo_uf:.2f} UF</span></div>', unsafe_allow_html=True)
    kpi_col3.markdown(f'<div class="kpi"><h3>Intereses Totales</h3><span>{interes_total:.2f} UF</span></div>', unsafe_allow_html=True)
    kpi_col4.markdown(f'<div class="kpi"><h3>Pie Inicial</h3><span>{pie_uf:.2f} UF</span></div>', unsafe_allow_html=True)

    # Gráfico anual capital vs interés (Plotly)
    years = list(anios_data.keys())
    interest_vals = [anios_data[y]["int"] for y in years]
    capital_vals = [anios_data[y]["cap"] for y in years]

    fig = go.Figure()
    fig.add_trace(go.Bar(name='Interés', x=years, y=interest_vals, marker_color='orange'))
    fig.add_trace(go.Bar(name='Capital', x=years, y=capital_vals, marker_color='teal'))
    fig.update_layout(barmode='stack', title='Evolución anual: Interés vs Capital', xaxis_title='Año', yaxis_title='UF pagadas')
    st.plotly_chart(fig, use_container_width=True)

    # Tabla amortización
    df = pd.DataFrame(tabla, columns=["Mes", "Año", "Capital UF", "Interés UF", "Saldo UF"])
    with st.expander("📅 Ver tabla de amortización"):
        st.dataframe(df.style.format({"Capital UF":"{:.2f}","Interés UF":"{:.2f}","Saldo UF":"{:.2f}"}), height=350)

    # Mensaje recomendación
    if tasa_anual < 4.5 and (pie_uf / precio_uf) * 100 >= 20:
        st.success("✅ Excelente combinación de tasa y pie.")
    elif (pie_uf / precio_uf) * 100 < 15:
        st.warning("⚠️ El pie es un poco bajo. Considera aumentarlo.")
    elif tasa_anual > 5.0:
        st.warning("⚠️ La tasa es alta. Intenta negociar una mejor con tu banco.")

# --- Footer ---
st.markdown("""
<footer style="text-align:center; margin-top: 30px; font-size: 0.8rem; color: gray;">
    Simulador Hipotecario Avanzado by Adolf &copy; 2025
</footer>
""", unsafe_allow_html=True)
