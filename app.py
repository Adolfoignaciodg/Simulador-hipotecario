import streamlit as st
import numpy as np
import pandas as pd
import requests
import plotly.graph_objects as go

# --- Configuración inicial ---
st.set_page_config(page_title="🏡 Simulador Hipotecario Avanzado by Adolf", layout="wide")
st.markdown("<h1 style='text-align: center; color: #2E86C1;'>🏡 Simulador Hipotecario Avanzado <span style='font-size: 20px;'>by Adolf</span></h1>", unsafe_allow_html=True)
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
        anio_salto = None

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
            if not anio_salto and capital > interes:
                anio_salto = anio

        # Resultados
        st.subheader("📊 Resultados")
        c1, c2 = st.columns(2)
        with c1:
            st.metric("Monto del crédito", f"{credito_uf:,.2f} UF", f"~{credito_uf * uf_clp:,.0f} CLP")
            st.metric("Dividendo mensual", f"{dividendo_uf:,.2f} UF", f"~{dividendo_clp:,.0f} CLP")
        with c2:
            st.metric("Intereses totales", f"{interes_total:,.2f} UF", f"~{interes_total * uf_clp:,.0f} CLP")
            st.metric("Sueldo requerido (25%)", f"~{sueldo_recomendado:,.0f} CLP")

        # Pie chart elegante (Plotly)
        fig1 = go.Figure(data=[go.Pie(labels=["Capital", "Interés"],
                                      values=[capital_total, interes_total],
                                      hole=0.4)])
        fig1.update_layout(title="Distribución total del pago", height=400)
        st.plotly_chart(fig1, use_container_width=True)

        # Barras anuales
        years = list(anios.keys())
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(x=years, y=[anios[y]["int"] for y in years], name="Interés", marker_color="orange"))
        fig2.add_trace(go.Bar(x=years, y=[anios[y]["cap"] for y in years], name="Capital", marker_color="teal"))
        fig2.update_layout(barmode='stack', title="Evolución anual: Interés vs Capital", xaxis_title="Año", yaxis_title="UF")
        st.plotly_chart(fig2, use_container_width=True)

        # Recomendación automática
        st.subheader("🧠 Recomendación rápida")
        if tasa_anual < 0.045 and pie_uf / precio_uf >= 0.2:
            st.success("✅ Buena combinación de tasa y pie inicial.")
        elif pie_uf / precio_uf < 0.15:
            st.warning("⚠️ El pie inicial es bajo. Esto podría aumentar los intereses.")
        elif tasa_anual > 0.055:
            st.warning("⚠️ La tasa es alta. Compara con otros bancos.")

        # Tabla
        df = pd.DataFrame(tabla, columns=["Mes", "Año", "Capital Pagado UF", "Interés Pagado UF", "Saldo Restante UF"])
        with st.expander("📅 Ver tabla de amortización"):
            st.dataframe(df.style.format({"Capital Pagado UF": "{:.2f}", "Interés Pagado UF": "{:.2f}", "Saldo Restante UF": "{:.2f}"}), height=400)
            st.download_button("📥 Descargar tabla CSV", data=df.to_csv(index=False), file_name="amortizacion.csv")

# --- Modo Inversionista y Recomendador (borradores) ---
elif modo == "Inversionista":
    st.info("🔧 Modo Inversionista aún en desarrollo. Próximamente podrás simular arriendo vs dividendo.")
else:
    st.info("🧠 Modo Inteligente en construcción. Pronto te ayudará a encontrar el mejor escenario según tus metas.")
