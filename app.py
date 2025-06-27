import streamlit as st
import numpy as np
import pandas as pd
import requests
import plotly.graph_objects as go

# --- Estilo Premium ---
st.set_page_config(page_title="🏡 Simulador Hipotecario Avanzado by Adolf", layout="wide")
st.markdown("""
<style>
h1 {
    font-family: 'Segoe UI', sans-serif;
    color: #2E86C1;
}
[data-testid="metric-container"] {
    background-color: transparent !important;
    padding: 12px 0px;
    border: none !important;
    font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif !important;
    color: #2C3E50 !important;
    font-weight: 600 !important;
    font-size: 18px !important;
}
[data-testid="metric-value"] {
    font-weight: 700 !important;
    font-size: 24px !important;
    color: #1B2631 !important;
}
[data-testid="metric-subheader"] {
    font-weight: 500 !important;
    font-size: 14px !important;
    color: #566573 !important;
}
.stButton>button {
    background-color: #2E86C1;
    color: white;
    border-radius: 10px;
    padding: 10px 16px;
    font-weight: bold;
    border: none;
}
.stButton>button:hover {
    background-color: #1A5276;
}
input[type="number"], .stSlider, select {
    border-radius: 8px;
    border: 1px solid #ccc;
    padding: 5px;
}
.css-1d391kg, .css-1cypcdb {
    background-color: #ecf2f9;
}
.st-expander {
    background-color: #f1f6fb;
    border: 1px solid #cbdce8;
    border-radius: 10px;
}
.reportview-container .markdown-text-container {
    font-size: 16px;
    line-height: 1.6;
}
</style>
""", unsafe_allow_html=True)

# --- Título principal ---
st.markdown("<h1 style='text-align: center;'>🏡 Simulador Hipotecario Avanzado <span style='font-size: 20px;'>by Adolf</span></h1>", unsafe_allow_html=True)
st.markdown("---")

# --- Sidebar: Indicadores Económicos ---
with st.sidebar:
    st.markdown("### 📈 Indicadores Económicos")
    try:
        r = requests.get("https://mindicador.cl/api").json()
        st.metric("UF", f"${r['uf']['valor']:,.2f} CLP")
        st.metric("Dólar", f"${r['dolar']['valor']:,.2f} CLP")
        st.metric("IPC", f"{r['ipc']['valor']:.2f}%")
        st.metric("TPM", f"{r['tpm']['valor']:.2f}%")
        uf_clp = r['uf']['valor']
        tpm = r['tpm']['valor']
    except:
        st.warning("⚠️ No se pudo cargar indicadores en línea. Se usan valores por defecto.")
        uf_clp = 36000
        tpm = 6.0

# --- Modo de simulación ---
modo = st.radio("Selecciona tu modo", ["Comprador para vivir", "Inversionista", "🧠 Recomendador Inteligente"])

# --- Simulación: Comprador para vivir ---
if modo == "Comprador para vivir":
    col1, col2 = st.columns(2)
    with col1:
        precio_uf = st.number_input("💰 Precio vivienda (UF)", value=4000.0, min_value=1.0)
        pie_uf = st.number_input("💵 Pie inicial (UF)", value=precio_uf * 0.2,
                                 min_value=precio_uf * 0.1, max_value=precio_uf)
        plazo = st.slider("📅 Plazo (años)", 1, 30, 20)
    with col2:
        tasa_anual = st.number_input("📊 Tasa interés anual (%)", value=4.0, step=0.1) / 100
        inflacion = st.number_input("📈 Inflación esperada (%)", value=3.0, step=0.1) / 100
        seguro_mensual = st.number_input("🛡️ Seguro mensual (CLP)", value=10000, step=1000)

    prepago = st.checkbox("¿Agregar prepago parcial?")
    if prepago:
        prepago_monto = st.number_input("💸 Monto prepago (UF)", value=0.0, min_value=0.0)
        prepago_ano = st.number_input("📆 Año del prepago", 1, plazo, 5)
    else:
        prepago_monto, prepago_ano = 0, 0

    if st.button("🔄 Calcular Crédito"):
        credito_uf = precio_uf - pie_uf
        tasa_mensual = (1 + tasa_anual)**(1/12) - 1
        n_meses = plazo * 12
        dividendo_uf = credito_uf * tasa_mensual / (1 - (1 + tasa_mensual)**-n_meses)
        dividendo_clp = dividendo_uf * uf_clp + seguro_mensual
        sueldo_recomendado = dividendo_clp / 0.25

        saldo = credito_uf
        interes_total = capital_total = 0
        tabla = []
        anios = {}

        for mes in range(1, n_meses + 1):
            interes = saldo * tasa_mensual
            capital = dividendo_uf - interes
            if prepago and mes == prepago_ano * 12:
                saldo -= prepago_monto
            saldo -= capital
            interes_total += interes
            capital_total += capital
            anio = mes // 12 + 1
            anios.setdefault(anio, {"cap": 0, "int": 0})
            anios[anio]["cap"] += capital
            anios[anio]["int"] += interes
            tabla.append([mes, anio, capital, interes, saldo])

        monto_total_uf = capital_total + interes_total
        monto_total_clp = monto_total_uf * uf_clp

        # --- Resultados ---
        st.subheader("📊 Resultados")
        c1, c2 = st.columns(2)
        with c1:
            st.metric("Monto del crédito", f"{credito_uf:,.2f} UF", f"~{credito_uf * uf_clp:,.0f} CLP")
            st.metric("Dividendo mensual", f"{dividendo_uf:,.2f} UF", f"~{dividendo_clp:,.0f} CLP")
            st.metric("Monto total a pagar (capital + interés)", f"{monto_total_uf:,.2f} UF", f"~{monto_total_clp:,.0f} CLP")
        with c2:
            st.metric("Intereses totales", f"{interes_total:,.2f} UF", f"~{interes_total * uf_clp:,.0f} CLP")
            st.metric("Sueldo requerido (25%)", f"~{sueldo_recomendado:,.0f} CLP")

        # --- Comparativa rápida de plazos ---
        st.subheader("📊 Comparativa rápida: distintos plazos con misma tasa simulada")
        plazos_comunes = [15, 20, 25, 30]
        comparacion_rapida = []

        for p in plazos_comunes:
            if p == plazo:
                continue
            meses_ref = p * 12
            tasa_mensual_ref = (1 + tasa_anual) ** (1/12) - 1
            dividendo_uf_ref = credito_uf * tasa_mensual_ref / (1 - (1 + tasa_mensual_ref) ** -meses_ref)
            dividendo_clp_ref = dividendo_uf_ref * uf_clp + seguro_mensual
            renta_recomendada = dividendo_clp_ref / 0.25
            total_uf = dividendo_uf_ref * meses_ref
            intereses_uf = total_uf - credito_uf
            total_clp = total_uf * uf_clp
            intereses_clp = intereses_uf * uf_clp

            comparacion_rapida.append([
                f"{p} años",
                f"{tasa_anual * 100:.2f}%",
                f"{dividendo_uf_ref:.2f} UF",
                f"${dividendo_clp_ref:,.0f}",
                f"${renta_recomendada:,.0f}",
                f"{total_uf:.2f} UF",
                f"${total_clp:,.0f}",
                f"{intereses_uf:.2f} UF",
                f"${intereses_clp:,.0f}"
            ])

        df_comp = pd.DataFrame(comparacion_rapida, columns=[
            "Plazo",
            "Tasa (%)",
            "Dividendo (UF)",
            "Dividendo ($)",
            "Renta sugerida ($)",
            "Monto total pagar (UF)",
            "Monto total pagar ($)",
            "Intereses Totales (UF)",
            "Intereses Totales ($)"
        ])
        st.dataframe(df_comp, height=380, use_container_width=True)
        st.caption(f"*Valores con tasa {tasa_anual*100:.2f}% y UF = ${uf_clp:,.2f} al {pd.Timestamp.now().strftime('%d-%m-%Y')}*")

        # --- Diagnóstico financiero, gráficos y tabla ---
        # (todo lo demás que ya tenías lo puedes dejar igual abajo de esto)

# --- Otros modos ---
elif modo == "Inversionista":
    st.info("🔧 Modo Inversionista aún en desarrollo. Pronto podrás simular arriendo vs dividendo.")
else:
    st.info("🧠 Modo Inteligente en construcción. Pronto te ayudará a encontrar el mejor escenario según tus metas.")
