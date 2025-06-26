import streamlit as st
import numpy as np
import pandas as pd
import requests
import matplotlib.pyplot as plt

# --- Configuración ---
st.set_page_config(page_title="🏡 Simulador Hipotecario Avanzado by Adolf", layout="wide")
st.title("🏡 Simulador Hipotecario Avanzado by Adolf")

# --- Indicadores: UF, TPM, IPC, Dólar ---
try:
    resp = requests.get("https://mindicador.cl/api")
    data = resp.json()
    uf_clp = data["uf"]["valor"]
    tpm = data.get("tpm", {}).get("valor", None)
    ipc = data.get("ipc", {}).get("valor", None)
    dolar = data.get("dolar", {}).get("valor", None)
except:
    uf_clp = 36000
    tpm = ipc = dolar = None

col1, col2, col3, col4 = st.columns(4)
col1.metric("UF (CLP)", f"{uf_clp:,.0f}")
if tpm is not None:
    col2.metric("TPM (%)", f"{tpm:.2f}")
else:
    col2.markdown("TPM no disponible")
if ipc is not None:
    col3.metric("IPC (%)", f"{ipc:.2f}")
else:
    col3.markdown("IPC no disponible")
if dolar is not None:
    col4.metric("Dólar (CLP)", f"{dolar:,.0f}")
else:
    col4.markdown("Dólar no disponible")

# --- Modos de simulación ---
modo = st.radio("Selecciona tu modo", ["Comprador para vivir", "Inversionista", "🧠 Recomendador Inteligente"])

# --- 1. Comprador para vivir ---
if modo == "Comprador para vivir":
    col1, col2 = st.columns(2)
    with col1:
        precio_uf = st.number_input("Precio de la vivienda (UF)", value=4000.0, min_value=1.0)
        pie_uf = st.number_input("Pie inicial (UF)", value=precio_uf * 0.2,
                                 min_value=precio_uf * 0.1, max_value=precio_uf)
        plazo = st.slider("Plazo del crédito (años)", min_value=1, max_value=30, value=20)
    with col2:
        tasa_anual = st.number_input("Tasa de interés anual (%)", value=4.0) / 100
        inflacion = st.number_input("Inflación estimada anual (%)", value=3.0) / 100
        seguro_mensual = st.number_input("Seguro mensual estimado (CLP)", value=10000)

    prepago = st.checkbox("¿Simular prepago parcial?")
    prepago_monto = prepago_ano = 0
    if prepago:
        prepago_monto = st.number_input("Monto prepago parcial (UF)", min_value=0.0, value=0.0)
        prepago_ano = st.number_input("Año del prepago", min_value=1, max_value=plazo, value=5)

    if st.button("🔄 Calcular Crédito"):
        # Cálculos
        credito_uf = max(precio_uf - pie_uf, 0)
        credito_porcentaje = credito_uf / precio_uf * 100
        pie_porcentaje = pie_uf / precio_uf * 100
        tasa_mensual = (1 + tasa_anual)**(1/12) - 1
        n_meses = plazo * 12
        dividendo_uf = credito_uf * tasa_mensual / (1 - (1 + tasa_mensual)**-n_meses) if credito_uf else 0
        dividendo_clp = dividendo_uf * uf_clp + seguro_mensual
        sueldo_req = dividendo_clp / 0.25

        # Amortización
        saldo = credito_uf
        interes_total = capital_total = 0
        anios_data = {}
        anio_salto = None
        tabla = []

        for mes in range(1, n_meses + 1):
            interes = saldo * tasa_mensual
            capital = dividendo_uf - interes
            if prepago and mes == prepago_ano * 12:
                saldo -= prepago_monto
            saldo -= capital
            interes_total += interes
            capital_total += capital
            anio = mes // 12 + 1
            anios_data.setdefault(anio, {"int": 0, "cap": 0})
            anios_data[anio]["int"] += interes
            anios_data[anio]["cap"] += capital
            tabla.append([mes, anio, capital, interes, saldo])
            if not anio_salto and capital > interes:
                anio_salto = anio

        monto_total_uf = capital_total + interes_total
        monto_total_clp = monto_total_uf * uf_clp

        # Resultados
        st.subheader("📊 Resultados del Crédito")
        c1, c2 = st.columns(2)
        with c1:
            st.metric("Monto del crédito", f"{credito_uf:.2f} UF", f"~{credito_uf*uf_clp:,.0f} CLP")
            st.markdown(f"Equivale al **{credito_porcentaje:.1f}%** del precio")
            st.metric("Dividendo mensual", f"{dividendo_uf:.2f} UF", f"~{dividendo_clp:,.0f} CLP")
            st.metric("Monto total a pagar (UF)", f"{monto_total_uf:.2f} UF", f"~{monto_total_clp:,.0f} CLP")
        with c2:
            st.metric("Pie inicial", f"{pie_uf:.2f} UF", f"~{pie_uf*uf_clp:,.0f} CLP")
            st.markdown(f"Representa **{pie_porcentaje:.1f}%** del precio")
            st.metric("Intereses totales", f"{interes_total:.2f} UF", f"~{interes_total*uf_clp:,.0f} CLP")
            st.metric("Sueldo estimado mínimo", f"~{sueldo_req:,.0f} CLP")

        # Gráfico circular (compacto)
        fig1, ax1 = plt.subplots(figsize=(4, 4))
        ax1.pie([capital_total, interes_total], labels=["Capital", "Interés"], autopct="%1.1f%%", startangle=90)
        ax1.set_title("Distribución pago total")
        st.pyplot(fig1)

        # Gráfico anual Capital vs Interés
        years = list(anios_data.keys())
        ints = [anios_data[y]["int"] for y in years]
        caps = [anios_data[y]["cap"] for y in years]
        fig2, ax2 = plt.subplots(figsize=(8, 4))
        ax2.bar(years, ints, label="Interés", color="orange")
        ax2.bar(years, caps, bottom=ints, label="Capital", color="teal")
        ax2.set_xlabel("Año")
        ax2.set_ylabel("UF pagadas")
        ax2.set_title("Evolución anual: Interés vs Capital")
        ax2.legend()
        st.pyplot(fig2)

        # Recomendación automática
        st.subheader("🧠 Recomendación automática")
        if tasa_anual < 0.045 and pie_porcentaje >= 20:
            st.success("✅ Excelente combinación de tasa y pie.")
        elif pie_porcentaje < 15:
            st.warning("⚠️ El pie es un poco bajo. Considera aumentarlo.")
        elif tasa_anual > 0.05:
            st.warning("⚠️ La tasa es alta. Intenta negociar una mejor con tu banco.")

        # Tabla de amortización
        df_tabla = pd.DataFrame(tabla, columns=["Mes", "Año", "Capital UF", "Interés UF", "Saldo UF"])
        with st.expander("📅 Ver tabla de amortización"):
            st.dataframe(df_tabla.style.format({"Capital UF": "{:.2f}", "Interés UF": "{:.2f}", "Saldo UF": "{:.2f}"}), height=400)
            st.download_button("📥 Descargar tabla en CSV", data=df_tabla.to_csv(index=False), file_name="amortizacion.csv", mime="text/csv")

# --- 2. Inversionista (sin cambios) ---
elif modo == "Inversionista":
    st.info("Modo Inversionista cargado. Pronto se optimizará.")

# --- 3. Recomendador Inteligente (sin cambios) ---
else:
    st.info("Modo Recomendador Inteligente cargado. En próximas versiones incluirá IA.")
