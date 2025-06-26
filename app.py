import streamlit as st
import numpy as np
import pandas as pd
import requests
import matplotlib.pyplot as plt

# --- Configuración general ---
st.set_page_config(page_title="🏡 Simulador Hipotecario Avanzado by Adolf", layout="wide")
st.markdown("<h1 style='text-align: center;'>🏡 Simulador Hipotecario Avanzado <br><span style='color:gray;'>by Adolf</span></h1>", unsafe_allow_html=True)
st.markdown("---")

# --- Indicadores económicos ---
try:
    resp = requests.get("https://mindicador.cl/api")
    data = resp.json()
    uf_clp = data["uf"]["valor"]
    tpm = data["tpm"]["valor"]
    ipc = data["ipc"]["valor"]
    dolar = data["dolar"]["valor"]
except:
    uf_clp = 36000
    tpm = ipc = dolar = None

st.markdown("### 📈 Indicadores Económicos")
coluf, coltpm, colipc, coldol = st.columns(4)
coluf.metric("UF", f"{uf_clp:,.2f} CLP")
coltpm.metric("TPM", f"{tpm:.2f}%" if tpm else "N/D")
colipc.metric("IPC", f"{ipc:.2f}%" if ipc else "N/D")
coldol.metric("Dólar", f"{dolar:,.2f} CLP" if dolar else "N/D")

st.markdown("---")

# --- Modo: Comprador para vivir ---
st.subheader("🧾 Datos de la Vivienda")
col1, col2 = st.columns(2)
with col1:
    precio_uf = st.number_input("Precio vivienda (UF)", value=4000.0, min_value=100.0)
    pie_uf = st.number_input("Pie inicial (UF)", value=precio_uf * 0.2,
                             min_value=precio_uf * 0.1, max_value=precio_uf)
    plazo = st.slider("Plazo del crédito (años)", 1, 30, 20)
with col2:
    tasa_anual = st.number_input("Tasa de interés anual (%)", value=4.0, min_value=0.1, max_value=15.0) / 100
    inflacion = st.number_input("Inflación anual estimada (%)", value=3.0) / 100
    seguro_mensual = st.number_input("Seguro mensual estimado (CLP)", value=10000)

prepago = st.checkbox("¿Simular prepago parcial?")
prepago_monto = prepago_ano = 0
if prepago:
    prepago_monto = st.number_input("Monto del prepago (UF)", value=0.0)
    prepago_ano = st.number_input("Año del prepago", min_value=1, max_value=plazo, value=5)

if st.button("🔄 Calcular Crédito"):
    credito_uf = max(precio_uf - pie_uf, 0)
    tasa_mensual = (1 + tasa_anual)**(1/12) - 1
    n_meses = plazo * 12
    dividendo_uf = credito_uf * tasa_mensual / (1 - (1 + tasa_mensual)**-n_meses)
    dividendo_clp = dividendo_uf * uf_clp + seguro_mensual
    sueldo_req = dividendo_clp / 0.25

    # Amortización
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
        anio = (mes - 1) // 12 + 1
        anios.setdefault(anio, {"int": 0, "cap": 0})
        anios[anio]["int"] += interes
        anios[anio]["cap"] += capital
        tabla.append([mes, anio, capital, interes, saldo])

    df = pd.DataFrame(tabla, columns=["Mes", "Año", "Capital UF", "Interés UF", "Saldo UF"])

    # --- Resultados clave ---
    st.markdown("## 📊 Resultados del Crédito")
    c1, c2 = st.columns(2)
    with c1:
        st.metric("Monto del crédito", f"{credito_uf:.2f} UF", f"~{credito_uf*uf_clp:,.0f} CLP")
        st.metric("Dividendo mensual", f"{dividendo_uf:.2f} UF", f"~{dividendo_clp:,.0f} CLP")
    with c2:
        st.metric("Intereses totales", f"{interes_total:.2f} UF", f"~{interes_total*uf_clp:,.0f} CLP")
        st.metric("Sueldo requerido (25%)", f"~{sueldo_req:,.0f} CLP")

    # --- Gráfico circular limpio ---
    fig1, ax1 = plt.subplots(figsize=(3.5, 3.5))
    ax1.pie([capital_total, interes_total], labels=["Capital", "Interés"],
            autopct="%1.1f%%", startangle=90, colors=["#66c2a5", "#fc8d62"])
    ax1.set_title("Distribución del Pago Total", fontsize=12)
    st.pyplot(fig1)

    # --- Gráfico anual Interés vs Capital ---
    st.markdown("### 📉 Evolución anual: Capital vs Interés")
    years = list(anios.keys())
    intereses = [anios[y]["int"] for y in years]
    capitales = [anios[y]["cap"] for y in years]
    fig2, ax2 = plt.subplots(figsize=(7, 3.5))
    ax2.bar(years, intereses, label="Interés", color="#fc8d62")
    ax2.bar(years, capitales, bottom=intereses, label="Capital", color="#66c2a5")
    ax2.set_xlabel("Año"); ax2.set_ylabel("UF pagadas")
    ax2.legend(); ax2.grid(True, linestyle="--", alpha=0.3)
    st.pyplot(fig2)

    # --- Tabla y descarga ---
    with st.expander("📅 Tabla de amortización"):
        st.dataframe(df.style.format({"Capital UF": "{:.2f}", "Interés UF": "{:.2f}", "Saldo UF": "{:.2f}"}), height=400)
        st.download_button("📥 Descargar CSV", df.to_csv(index=False), file_name="amortizacion.csv", mime="text/csv")
