import streamlit as st
import numpy as np
import pandas as pd
import requests
import matplotlib.pyplot as plt
from fpdf import FPDF
import base64
import tempfile

# --- Configuración inicial ---
st.set_page_config(page_title="🏡 Simulador Hipotecario Avanzado by ADOLF", layout="wide")
st.title("🏡 Simulador Hipotecario Avanzado by ADOLF")

# --- Valor UF ---
try:
    uf_clp = requests.get("https://mindicador.cl/api").json()["uf"]["valor"]
except:
    uf_clp = 36000
st.markdown(f"**Valor UF hoy:** {uf_clp:,.2f} CLP")

# --- Selección de perfil ---
perfil = st.radio("Selecciona tu perfil", ["Comprador para vivir", "Inversionista"])
st.markdown(f"**Perfil seleccionado:** `{perfil}`")

# --- Entradas usuario ---
col1, col2 = st.columns(2)
with col1:
    precio_uf = st.number_input("Precio de la vivienda (UF)", value=4000.0, min_value=1.0)
    pie_minimo = precio_uf * 0.1
    pie_uf = st.number_input("Pie inicial (UF)", value=800.0, min_value=pie_minimo, max_value=precio_uf)
    plazo = st.slider("Plazo del crédito (años)", min_value=1, max_value=30, value=20)
with col2:
    tasa_anual = st.number_input("Tasa de interés anual (%)", value=4.0) / 100
    inflacion = st.number_input("Inflación esperada anual (%)", value=3.0) / 100
    seguro_mensual = st.number_input("Seguro mensual estimado (CLP)", value=10000)

# --- Prepago parcial ---
prepago = st.checkbox("¿Simular prepago parcial?")
prepago_monto, prepago_ano = 0.0, 0
if prepago:
    prepago_monto = st.number_input("Monto de prepago parcial (UF)", min_value=0.0, value=0.0)
    prepago_ano = st.number_input("Año en que harás prepago", min_value=1, max_value=plazo, value=5)

# --- Botón para calcular ---
if st.button("🔄 Calcular Crédito"):

    # --- Cálculos ---
    credito_uf = max(precio_uf - pie_uf, 0)
    credito_porcentaje = (credito_uf / precio_uf) * 100 if precio_uf > 0 else 0
    pie_porcentaje = (pie_uf / precio_uf) * 100 if precio_uf > 0 else 0

    tasa_mensual = (1 + tasa_anual)**(1/12) - 1
    n_meses = plazo * 12
    dividendo_uf = (credito_uf * tasa_mensual) / (1 - (1 + tasa_mensual)**-n_meses) if credito_uf > 0 else 0
    dividendo_clp = dividendo_uf * uf_clp + seguro_mensual
    sueldo_necesario = dividendo_clp / 0.25

    # --- Tabla de amortización ---
    saldo = credito_uf
    tabla = []
    interes_total = 0
    capital_total = 0
    anio_salto = None
    resumen_anual = {}

    for mes in range(1, n_meses + 1):
        interes_mes = saldo * tasa_mensual
        capital_mes = dividendo_uf - interes_mes

        if prepago and mes == prepago_ano * 12:
            saldo -= prepago_monto

        saldo -= capital_mes
        interes_total += interes_mes
        capital_total += capital_mes

        if not anio_salto and capital_mes > interes_mes:
            anio_salto = mes // 12 + 1

        anio = mes // 12 + 1
        resumen_anual.setdefault(anio, {"interes": 0, "capital": 0})
        resumen_anual[anio]["interes"] += interes_mes
        resumen_anual[anio]["capital"] += capital_mes

        tabla.append([mes, anio, capital_mes, interes_mes, dividendo_uf, saldo, capital_total, interes_total])

    df = pd.DataFrame(tabla, columns=[
        "Mes", "Año", "Capital Pagado UF", "Interés Pagado UF",
        "Dividendo UF", "Saldo Pendiente UF", "Capital Acum UF", "Interés Acum UF"
    ])

    # --- Resultados ---
    st.subheader("📊 Resultados del Crédito")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Monto del crédito", f"{credito_uf:,.2f} UF", f"~{credito_uf * uf_clp:,.0f} CLP")
        st.markdown(f"📊 Esto equivale al **{credito_porcentaje:.1f}%** del precio de la vivienda.")
        st.metric("Dividendo mensual", f"{dividendo_uf:,.2f} UF", f"~{dividendo_clp:,.0f} CLP")
    with col2:
        st.metric("Pie inicial", f"{pie_uf:,.2f} UF", f"~{pie_uf * uf_clp:,.0f} CLP")
        st.markdown(f"📊 Esto equivale al **{pie_porcentaje:.1f}%** del precio de la vivienda.")
        st.metric("Intereses totales", f"{interes_total:,.2f} UF", f"~{interes_total * uf_clp:,.0f} CLP")
        st.metric("Sueldo requerido (25%)", f"~{sueldo_necesario:,.0f} CLP")

    if perfil == "Comprador para vivir" and anio_salto:
        st.info(f"📌 A partir del **año {anio_salto}** pagarás más capital que intereses.")

    # --- Tabla y descarga CSV ---
    with st.expander("📅 Ver tabla de amortización"):
        st.dataframe(df.style.format({
            "Capital Pagado UF": "{:.2f}", "Interés Pagado UF": "{:.2f}",
            "Dividendo UF": "{:.2f}", "Saldo Pendiente UF": "{:.2f}",
            "Capital Acum UF": "{:.2f}", "Interés Acum UF": "{:.2f}"
        }), height=400)
        st.download_button("📥 Descargar tabla en CSV", data=df.to_csv(index=False), file_name="amortizacion.csv", mime="text/csv")

    # --- Gráfico Pie ---
    fig1, ax1 = plt.subplots()
    ax1.pie([capital_total, interes_total], labels=["Capital", "Interés"], autopct="%1.1f%%", startangle=90)
    ax1.set_title("Distribución total del pago")
    st.pyplot(fig1)

    # --- Gráfico Interés vs Capital por año ---
    st.subheader("📈 Evolución Anual Capital vs Interés")
    años = list(resumen_anual.keys())
    capitales = [resumen_anual[a]["capital"] for a in años]
    intereses = [resumen_anual[a]["interes"] for a in años]

    fig2, ax2 = plt.subplots()
    ax2.bar(años, capitales, label="Capital", color="#4CAF50")
    ax2.bar(años, intereses, bottom=capitales, label="Interés", color="#F44336")
    ax2.set_xlabel("Año")
    ax2.set_ylabel("Monto en UF")
    ax2.set_title("Capital vs Interés por Año")
    ax2.legend()
    st.pyplot(fig2)

    # --- Exportar a PDF ---
    def exportar_pdf():
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        pdf.cell(200, 10, "Simulador Hipotecario Avanzado by ADOLF", ln=True, align="C")
        pdf.set_font("Arial", "", 12)
        pdf.cell(200, 10, f"Valor UF: {uf_clp:,.0f} CLP", ln=True)
        pdf.cell(200, 10, f"Monto Crédito: {credito_uf:,.2f} UF (~{credito_uf * uf_clp:,.0f} CLP)", ln=True)
        pdf.cell(200, 10, f"Pie Inicial: {pie_uf:,.2f} UF (~{pie_uf * uf_clp:,.0f} CLP)", ln=True)
        pdf.cell(200, 10, f"Dividendo mensual aprox: {dividendo_uf:,.2f} UF (~{dividendo_clp:,.0f} CLP)", ln=True)
        pdf.set_text_color(220, 220, 220)
        pdf.set_font("Arial", "B", 50)
        pdf.rotate(45)
        pdf.text(30, 200, "Simulado por App ADOLF")
        pdf.rotate(0)
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        pdf.output(tmp.name)
        with open(tmp.name, "rb") as f:
            pdf_data = f.read()
        b64 = base64.b64encode(pdf_data).decode()
        href = f'<a href="data:application/pdf;base64,{b64}" download="simulacion.pdf">📄 Descargar PDF</a>'
        st.markdown(href, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 🧾 Exportar a PDF")
    exportar_pdf()
