import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go

# --- Configuración general ---
st.set_page_config(page_title="🏡 Simulador Hipotecario Avanzado by Adolf", layout="wide")
st.markdown("<h1 style='text-align: center;'>🏡 Simulador Hipotecario Avanzado <span style='color:#555;'>by Adolf</span></h1>", unsafe_allow_html=True)
st.write("---")

# --- Indicadores económicos (compacto y elegante) ---
try:
    data = requests.get("https://mindicador.cl/api").json()
    uf = data["uf"]["valor"]
    tpm = data["tpm"]["valor"]
    dolar = data["dolar"]["valor"]
    ipc = data["ipc"]["valor"]
except:
    uf, tpm, dolar, ipc = 36000, 5.0, 900, 3.0

st.markdown("### 📈 Indicadores Económicos")
col1, col2, col3, col4 = st.columns(4)
col1.metric("💰 UF", f"{uf:,.2f} CLP")
col2.metric("🏦 TPM", f"{tpm:.2f} %")
col3.metric("💵 Dólar", f"{dolar:,.2f} CLP")
col4.metric("📉 IPC", f"{ipc:.2f} %")
st.caption("Fuente: mindicador.cl")
st.write("---")

# --- Modo: Comprador para vivir ---
st.subheader("🧾 Simulación para Comprador de Vivienda")

col1, col2 = st.columns(2)
with col1:
    precio_uf = st.number_input("Precio vivienda (UF)", value=4000.0, min_value=1.0)
    pie_uf = st.number_input("Pie inicial (UF)", value=precio_uf * 0.2, min_value=precio_uf * 0.1, max_value=precio_uf)
    plazo = st.slider("Plazo (años)", min_value=5, max_value=30, value=20)
with col2:
    tasa_anual = st.number_input("Tasa interés anual (%)", value=4.0, min_value=0.1, max_value=15.0) / 100
    inflacion = st.number_input("Inflación esperada (%)", value=3.0) / 100
    seguro = st.number_input("Seguro mensual (CLP)", value=10000)

prepago = st.checkbox("¿Simular prepago parcial?")
prepago_monto = prepago_ano = 0
if prepago:
    prepago_monto = st.number_input("Monto prepago (UF)", min_value=0.0, value=0.0)
    prepago_ano = st.slider("Año del prepago", min_value=1, max_value=plazo, value=5)

if st.button("🔄 Calcular Crédito"):

    # Cálculos iniciales
    credito_uf = precio_uf - pie_uf
    tasa_mensual = (1 + tasa_anual)**(1/12) - 1
    n_meses = plazo * 12
    dividendo_uf = credito_uf * tasa_mensual / (1 - (1 + tasa_mensual)**-n_meses)
    dividendo_clp = dividendo_uf * uf + seguro
    sueldo_necesario = dividendo_clp / 0.25

    saldo = credito_uf
    total_int = total_cap = 0
    tabla = []
    resumen_anual = {}
    anio_salto = None

    for mes in range(1, n_meses + 1):
        interes = saldo * tasa_mensual
        capital = dividendo_uf - interes
        if prepago and mes == prepago_ano * 12:
            saldo -= prepago_monto
        saldo -= capital
        total_int += interes
        total_cap += capital
        anio = mes // 12 + 1
        resumen_anual.setdefault(anio, {"int": 0, "cap": 0})
        resumen_anual[anio]["int"] += interes
        resumen_anual[anio]["cap"] += capital
        tabla.append([mes, anio, capital, interes, saldo])
        if not anio_salto and capital > interes:
            anio_salto = anio

    df = pd.DataFrame(tabla, columns=["Mes", "Año", "Capital UF", "Interés UF", "Saldo UF"])

    # Resultados
    st.subheader("📊 Resumen del Crédito")
    c1, c2 = st.columns(2)
    with c1:
        st.metric("🏦 Crédito solicitado", f"{credito_uf:.2f} UF", f"{credito_uf*uf:,.0f} CLP")
        st.metric("📉 Dividendo mensual", f"{dividendo_uf:.2f} UF", f"{dividendo_clp:,.0f} CLP")
    with c2:
        st.metric("💸 Interés total", f"{total_int:.2f} UF", f"{total_int*uf:,.0f} CLP")
        st.metric("💼 Sueldo mínimo estimado", f"{sueldo_necesario:,.0f} CLP")

    # Recomendación visual
    if tasa_anual < 0.045 and pie_uf / precio_uf >= 0.2:
        st.success("✅ Muy buena tasa y pie. Es un buen momento para financiar.")
    elif tasa_anual > 0.06:
        st.warning("⚠️ Tasa alta. Considera esperar o negociar.")
    elif pie_uf / precio_uf < 0.15:
        st.warning("⚠️ El pie es bajo. Es posible que la aprobación sea difícil.")

    if anio_salto:
        st.info(f"📌 Desde el año **{anio_salto}** pagarás más capital que interés.")

    # --- GRÁFICOS CON PLOTLY ---
    # Pie chart elegante
    fig_pie = go.Figure(data=[go.Pie(labels=["Capital", "Interés"],
                                     values=[total_cap, total_int],
                                     hole=0.4)])
    fig_pie.update_layout(title="Distribución total del crédito", height=350)
    st.plotly_chart(fig_pie, use_container_width=True)

    # Barras anuales
    years = list(resumen_anual.keys())
    fig_bar = go.Figure()
    fig_bar.add_trace(go.Bar(name="Interés", x=years, y=[resumen_anual[y]["int"] for y in years],
                             marker_color="orange"))
    fig_bar.add_trace(go.Bar(name="Capital", x=years, y=[resumen_anual[y]["cap"] for y in years],
                             marker_color="green"))
    fig_bar.update_layout(barmode='stack', title="Evolución anual de pagos (UF)",
                          xaxis_title="Año", yaxis_title="UF", height=400)
    st.plotly_chart(fig_bar, use_container_width=True)

    # Tabla amortización
    with st.expander("📅 Ver tabla completa de amortización"):
        st.dataframe(df.style.format({"Capital UF":"{:.2f}","Interés UF":"{:.2f}","Saldo UF":"{:.2f}"}), height=400)
        st.download_button("📥 Descargar tabla CSV", data=df.to_csv(index=False), file_name="amortizacion.csv")
