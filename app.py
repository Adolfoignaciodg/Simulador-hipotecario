import streamlit as st
import numpy as np
import pandas as pd
import requests
import matplotlib.pyplot as plt

# --- Configuración general ---
st.set_page_config(page_title="🏡 Simulador Hipotecario Avanzado by Adolf", layout="wide")
st.markdown("<h1 style='text-align: center;'>🏡 Simulador Hipotecario Avanzado <br><span style='color:gray;'>by Adolf</span></h1>", unsafe_allow_html=True)
st.markdown("---")

# --- Indicadores económicos desde mindicador.cl ---
try:
    r = requests.get("https://mindicador.cl/api")
    data = r.json()
    uf_clp = data["uf"]["valor"]
    tpm = data["tpm"]["valor"]
    ipc = data["ipc"]["valor"]
    dolar = data["dolar"]["valor"]
except:
    uf_clp = 36000
    tpm = ipc = dolar = None

# --- Mostrar indicadores ---
st.markdown("### 📈 Indicadores Económicos")
col1, col2, col3, col4 = st.columns(4)
col1.metric("UF", f"{uf_clp:,.2f} CLP")
col2.metric("TPM", f"{tpm:.2f}%" if tpm else "N/D")
col3.metric("IPC", f"{ipc:.2f}%" if ipc else "N/D")
col4.metric("Dólar", f"{dolar:,.2f} CLP" if dolar else "N/D")

st.markdown("---")

# --- Selección de modo ---
modo = st.radio("Selecciona tu modo", ["🏡 Comprador para vivir", "💼 Inversionista", "🧠 Recomendador Inteligente"])

# --- 1. COMPRADOR PARA VIVIR ---
if modo == "🏡 Comprador para vivir":
    st.subheader("🧾 Datos del Crédito Hipotecario")
    col1, col2 = st.columns(2)
    with col1:
        precio_uf = st.number_input("Precio vivienda (UF)", value=4000.0, min_value=100.0)
        pie_uf = st.number_input("Pie inicial (UF)", value=precio_uf * 0.2,
                                 min_value=precio_uf * 0.1, max_value=precio_uf)
        plazo = st.slider("Plazo del crédito (años)", 1, 30, 20)
    with col2:
        tasa_anual = st.number_input("Tasa de interés anual (%)", value=4.0, min_value=0.1, max_value=15.0) / 100
        inflacion = st.number_input("Inflación esperada anual (%)", value=3.0) / 100
        seguro_mensual = st.number_input("Seguro mensual estimado (CLP)", value=10000)

    # --- Prepago ---
    prepago = st.checkbox("¿Simular prepago parcial?")
    prepago_monto = prepago_ano = 0
    if prepago:
        prepago_monto = st.number_input("Monto prepago (UF)", value=0.0)
        prepago_ano = st.number_input("Año del prepago", min_value=1, max_value=plazo, value=5)

    # --- Cálculo ---
    if st.button("🔄 Calcular Crédito"):
        credito_uf = max(precio_uf - pie_uf, 0)
        tasa_mensual = (1 + tasa_anual)**(1/12) - 1
        n_meses = plazo * 12
        dividendo_uf = credito_uf * tasa_mensual / (1 - (1 + tasa_mensual)**-n_meses)
        dividendo_clp = dividendo_uf * uf_clp + seguro_mensual
        sueldo_recomendado = dividendo_clp / 0.25

        saldo = credito_uf
        capital_total = interes_total = 0
        anios = {}
        tabla = []

        for mes in range(1, n_meses + 1):
            interes = saldo * tasa_mensual
            capital = dividendo_uf - interes
            if prepago and mes == prepago_ano * 12:
                saldo -= prepago_monto
            saldo -= capital
            capital_total += capital
            interes_total += interes
            anio = (mes - 1) // 12 + 1
            anios.setdefault(anio, {"int": 0, "cap": 0})
            anios[anio]["int"] += interes
            anios[anio]["cap"] += capital
            tabla.append([mes, anio, capital, interes, saldo])

        df = pd.DataFrame(tabla, columns=["Mes", "Año", "Capital UF", "Interés UF", "Saldo UF"])

        # --- Resultados y métricas ---
        st.markdown("## 📊 Resultados del Crédito")
        c1, c2 = st.columns(2)
        with c1:
            st.metric("Monto del crédito", f"{credito_uf:.2f} UF", f"~{credito_uf * uf_clp:,.0f} CLP")
            st.metric("Dividendo mensual", f"{dividendo_uf:.2f} UF", f"~{dividendo_clp:,.0f} CLP")
        with c2:
            st.metric("Intereses totales", f"{interes_total:.2f} UF", f"~{interes_total * uf_clp:,.0f} CLP")
            st.metric("Sueldo mínimo recomendado", f"~{sueldo_recomendado:,.0f} CLP")

        # --- Gráfico circular ---
        fig1, ax1 = plt.subplots(figsize=(3.5, 3.5))
        ax1.pie([capital_total, interes_total], labels=["Capital", "Interés"],
                autopct="%1.1f%%", startangle=90, colors=["#66c2a5", "#fc8d62"])
        ax1.set_title("Distribución total del pago")
        st.pyplot(fig1)

        # --- Gráfico anual de interés vs capital ---
        st.markdown("### 📉 Evolución anual: Capital vs Interés")
        years = list(anios.keys())
        intereses = [anios[y]["int"] for y in years]
        capitales = [anios[y]["cap"] for y in years]
        fig2, ax2 = plt.subplots(figsize=(7, 3.5))
        ax2.bar(years, intereses, label="Interés", color="#fc8d62")
        ax2.bar(years, capitales, bottom=intereses, label="Capital", color="#66c2a5")
        ax2.set_xlabel("Año")
        ax2.set_ylabel("UF pagadas")
        ax2.legend()
        ax2.grid(True, linestyle="--", alpha=0.3)
        st.pyplot(fig2)

        # --- Tabla amortización ---
        with st.expander("📅 Tabla de amortización"):
            st.dataframe(df.style.format({"Capital UF":"{:.2f}", "Interés UF":"{:.2f}", "Saldo UF":"{:.2f}"}), height=400)
            st.download_button("📥 Descargar en CSV", data=df.to_csv(index=False), file_name="amortizacion.csv", mime="text/csv")

# --- 2. INVERSIONISTA ---
elif modo == "💼 Inversionista":
    st.info("💼 Modo Inversionista: En construcción. Pronto más detalles.")

# --- 3. RECOMENDADOR INTELIGENTE ---
elif modo == "🧠 Recomendador Inteligente":
    st.info("🧠 Modo IA: Muy pronto te recomendaremos el mejor crédito según tus metas y sueldo.")
