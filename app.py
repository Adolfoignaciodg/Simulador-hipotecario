import streamlit as st
import numpy as np
import pandas as pd
import requests
import plotly.graph_objects as go

# --- Estilo Premium ---
st.set_page_config(page_title="Simulador Hipotecario 🏡", layout="wide")
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
st.markdown("<h1 style='text-align: center;'>Simulador Hipotecario<span style='font-size: 20px;'> _ </span></h1>", unsafe_allow_html=True)
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

# --- Inputs principales ---
precio_uf = st.number_input("💰 Precio vivienda (UF)", value=3045.0, min_value=1.0)
pie_uf = st.number_input("💵 Pie inicial (UF)", value=precio_uf * 0.2,
                         min_value=precio_uf * 0.1, max_value=precio_uf)
plazo = st.slider("📅 Plazo (años)", 1, 30, 20)
tasa_anual = st.number_input("📊 Tasa interés anual (%)", value=3.7, step=0.1) / 100
inflacion = st.number_input("📈 Inflación esperada (%)", value=3.0, step=0.1) / 100
seguro_mensual = st.number_input("🛡️ Seguro mensual (CLP)", value=10000, step=1000)

# Prepago opcional
prepago = st.checkbox("¿Agregar prepago parcial?")
if prepago:
    prepago_monto = st.number_input("💸 Monto prepago (UF)", value=0.0, min_value=0.0)
    prepago_ano = st.number_input("📆 Año del prepago", 1, plazo, 5)
else:
    prepago_monto, prepago_ano = 0, 0

# Beneficios/subsidios
def manejar_beneficios():
    st.markdown("### 🎁 Agregar beneficios, subsidios o descuentos")
    if "beneficios" not in st.session_state:
        st.session_state.beneficios = []
    with st.form("form_beneficios"):
        monto_benef = st.number_input("Monto beneficio (UF)", min_value=0.0, step=0.1, format="%.2f")
        desc_benef = st.text_input("Descripción del beneficio (opcional)")
        agregar_benef = st.form_submit_button("➕ Agregar beneficio")
    if agregar_benef and monto_benef > 0:
        st.session_state.beneficios.append({"monto": monto_benef, "desc": desc_benef})
    total_beneficios = sum(b["monto"] for b in st.session_state.beneficios)
    if st.session_state.beneficios:
        st.info(f"Total beneficios acumulados: **{total_beneficios:.2f} UF**")
        for idx, b in enumerate(st.session_state.beneficios):
            col1_b, col2_b = st.columns([0.8, 0.2])
            with col1_b:
                st.markdown(f"- {b['desc'] or 'Sin descripción'}: **{b['monto']:.2f} UF**")
            with col2_b:
                if st.button(f"❌ Eliminar", key=f"eliminar_benef_{idx}"):
                    st.session_state.beneficios.pop(idx)
                    st.experimental_rerun()
    return total_beneficios

total_beneficios = manejar_beneficios()

# --- Cálculos automáticos sin botón ---
credito_uf = max(precio_uf - pie_uf - total_beneficios, 0)
credito_clp = credito_uf * uf_clp
tasa_mensual = (1 + tasa_anual) ** (1/12) - 1
n_meses = plazo * 12
if credito_uf > 0:
    dividendo_uf = credito_uf * tasa_mensual / (1 - (1 + tasa_mensual) ** -n_meses)
else:
    dividendo_uf = 0
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

monto_total_uf = capital_total + interes_total
monto_total_clp = monto_total_uf * uf_clp

# CAP RATE: tasa de capitalización
arriendo_mensual = st.number_input("🏠 Arriendo mensual estimado (CLP)", value=0, step=10000)
arriendo_anual = arriendo_mensual * 12
cap_rate = (arriendo_anual / (precio_uf * uf_clp)) * 100 if precio_uf * uf_clp > 0 else 0

# --- Resultados ---
st.subheader("📊 Resultados")
c1, c2 = st.columns(2)
with c1:
    st.metric("Pie Inicial", f"{pie_uf:,.2f} UF", f"~${pie_uf * uf_clp:,.0f} CLP")
    st.metric("Monto total crédito pedido", f"{credito_uf:,.2f} UF", f"~${credito_clp:,.0f} CLP")
    st.metric("Dividendo mensual", f"{dividendo_uf:,.2f} UF", f"~${dividendo_clp:,.0f} CLP")
    st.metric("Monto total a pagar (crédito + interés)", f"{monto_total_uf:,.2f} UF", f"~${monto_total_clp:,.0f} CLP")
with c2:
    st.metric("Intereses totales", f"{interes_total:,.2f} UF", f"~${interes_total * uf_clp:,.0f} CLP")
    st.metric("Beneficios/Subsidios aplicados", f"{total_beneficios:.2f} UF")
    st.metric("Sueldo requerido (25%)", f"~${sueldo_recomendado:,.0f} CLP")
    st.metric("🏡 Cap Rate estimado", f"{cap_rate:.2f} %")

# --- Comparativa rápida de otros plazos ---
plazos_comunes = [15, 20, 25, 30]
comparacion = []

for p in plazos_comunes:
    meses_alt = p * 12
    tasa_mensual_alt = (1 + tasa_anual) ** (1/12) - 1
    if credito_uf > 0:
        dividendo_uf_alt = credito_uf * tasa_mensual_alt / (1 - (1 + tasa_mensual_alt) ** -meses_alt)
    else:
        dividendo_uf_alt = 0
    dividendo_clp_alt = dividendo_uf_alt * uf_clp + seguro_mensual
    renta_sugerida_alt = dividendo_clp_alt / 0.25
    total_pagar_uf = dividendo_uf_alt * meses_alt
    total_pagar_clp = dividendo_clp_alt * meses_alt
    interes_total_uf = total_pagar_uf - credito_uf
    interes_total_clp = interes_total_uf * uf_clp

    monto_total_con_pie_uf = pie_uf + total_pagar_uf
    monto_total_con_pie_clp = monto_total_con_pie_uf * uf_clp

    comparacion.append([
        f"{p} años",
        f"{tasa_anual*100:.2f} %",
        f"{dividendo_uf_alt:,.2f} UF ~ ${dividendo_clp_alt:,.0f}",
        f"{renta_sugerida_alt/uf_clp:,.2f} UF ~ ${renta_sugerida_alt:,.0f}",
        f"{total_pagar_uf:,.2f} UF ~ ${total_pagar_clp:,.0f}",
        f"{interes_total_uf:,.2f} UF ~ ${interes_total_clp:,.0f}",
        f"{monto_total_con_pie_uf:,.2f} UF ~ ${monto_total_con_pie_clp:,.0f}",
        "✔️ Simulado" if p == plazo else ""
    ])

df_comp = pd.DataFrame(comparacion, columns=[
    "↑ Plazo",
    "Tasa (%)",
    "Dividendo mensual (UF ~ CLP)",
    "Renta sugerida (UF ~ CLP)",
    "Monto total: credito+interes (UF ~ CLP)",
    "Intereses totales (UF ~ CLP)",
    "Monto total: credito+interés+Pie (UF ~ CLP)",
    "Simulado"
])

def highlight_simulado(row):
    return ['background-color: #D0E9FF; font-weight: bold;' if row['Simulado'] else '' for _ in row]

df_styled = df_comp.style.apply(highlight_simulado, axis=1)

st.markdown("### 📊 Comparativa rápida: distintos plazos con misma tasa")
st.dataframe(df_styled, use_container_width=True)
st.caption(f"*Comparativa estimada con tasa {tasa_anual*100:.2f}% y UF = ${uf_clp:,.2f} al {pd.Timestamp.now().strftime('%d-%m-%Y')}*")

# --- Gráficos ---
fig1 = go.Figure(data=[go.Pie(
    labels=["Pie Inicial", "Capital", "Interés"],
    values=[pie_uf, capital_total, interes_total],
    hole=0.4,
    marker=dict(colors=["#2980B9", "#1ABC9C", "#F39C12"]),
    customdata=[round(pie_uf * uf_clp), round(capital_total * uf_clp), round(interes_total * uf_clp)],
    hovertemplate="<b>%{label}</b><br>Monto: %{value:.2f} UF<br>~$%{customdata:,} CLP<extra></extra>"
)])
fig1.update_layout(title="Distribución total del pago (incluyendo Pie Inicial)", height=400, showlegend=True)
st.plotly_chart(fig1, use_container_width=True)

years = list(anios.keys())
fig2 = go.Figure()
fig2.add_trace(go.Bar(
    x=years,
    y=[anios[y]["int"] for y in years],
    name="Interés",
    marker_color="orange",
    customdata=[round(anios[y]["int"] * uf_clp) for y in years],
    hovertemplate="<b>Año %{x}</b><br>Interés: %{y:.2f} UF<br>(~$%{customdata:,} CLP)<extra></extra>"
))
fig2.add_trace(go.Bar(
    x=years,
    y=[anios[y]["cap"] for y in years],
    name="Capital",
    marker_color="teal",
    customdata=[round(anios[y]["cap"] * uf_clp) for y in years],
    hovertemplate="<b>Año %{x}</b><br>Capital: %{y:.2f} UF<br>(~$%{customdata:,} CLP)<extra></extra>"
))
fig2.update_layout(barmode='stack', title="📉 Evolución anual: Interés vs Capital",
                   xaxis_title="Año", yaxis_title="UF", height=450)
st.plotly_chart(fig2, use_container_width=True)

# Diagnóstico Financiero Inteligente
st.subheader("💡 Diagnóstico Financiero Inteligente")
diagnosticos = []
pie_pct = pie_uf / precio_uf if precio_uf > 0 else 0
ratio_total = monto_total_uf / credito_uf if credito_uf > 0 else float('inf')

if tasa_anual < 0.035:
    diagnosticos.append("🔵 Excelente tasa. Lograste condiciones muy competitivas.")
elif tasa_anual <= 0.045:
    diagnosticos.append("🟢 Buena tasa. Estás dentro del rango óptimo actual.")
elif tasa_anual <= 0.055:
    diagnosticos.append("🟡 Tasa aceptable, pero podrías buscar mejores opciones.")
else:
    diagnosticos.append("🔴 Tasa alta. Evalúa cotizar con otros bancos o esperar mejores condiciones.")

if pie_pct >= 0.25:
    diagnosticos.append("🔵 Excelente pie inicial. Reduciste el monto y los intereses del crédito.")
elif pie_pct >= 0.20:
    diagnosticos.append("🟢 Buen pie inicial. Cumples con lo recomendado por la banca.")
elif pie_pct >= 0.15:
    diagnosticos.append("🟡 Pie aceptable. Considera aumentarlo si puedes.")
else:
    diagnosticos.append("🔴 Pie muy bajo. Podrías enfrentar mayores intereses y restricciones.")

if plazo > 25:
    diagnosticos.append("🟡 Plazo largo. Cuotas más bajas, pero pagas más intereses.")
elif plazo < 15:
    diagnosticos.append("🟢 Plazo corto. Ahorro en intereses, pero cuota más exigente.")

if ratio_total > 2.0:
    diagnosticos.append("🔴 Estás pagando más del doble del crédito en total. Revisa la tasa y plazo.")
elif ratio_total > 1.7:
    diagnosticos.append("🟡 Costo total elevado. Ajustar plazo o tasa podría ayudar.")
else:
    diagnosticos.append("🟢 Costo total razonable. Bien controlado.")

if sueldo_recomendado > 2_000_000:
    diagnosticos.append("🟡 El dividendo requiere un ingreso mensual alto. Evalúa reducir el monto del crédito o aumentar el pie.")
elif sueldo_recomendado < 1_200_000:
    diagnosticos.append("🟢 Buena relación cuota / ingreso estimado. Deberías poder cumplir con holgura.")

for d in diagnosticos:
    st.markdown(f"- {d}")

# Tabla de amortización
df = pd.DataFrame(tabla, columns=["Mes", "Año", "Capital Pagado UF", "Interés Pagado UF", "Saldo Restante UF"])
with st.expander("📅 Ver tabla de amortización"):
    st.dataframe(df.style.format({
        "Capital Pagado UF": "{:.2f}",
        "Interés Pagado UF": "{:.2f}",
        "Saldo Restante UF": "{:.2f}"
    }), height=400)
    st.download_button("📥 Descargar tabla CSV", data=df.to_csv(index=False), file_name="amortizacion.csv")

st.markdown("---")
st.subheader("💼 Análisis de Capacidad de Repago (CAPRATE)")

ingreso_real = st.number_input(
    "Ingresa tu ingreso mensual líquido (CLP) para calcular CAPRATE (opcional)", min_value=0, step=10000, format="%d"
)

# Usamos el ingreso real si existe, si no, el recomendado (sueldo estimado)
if ingreso_real > 0:
    ingreso_usado = ingreso_real
    ingreso_label = "tu ingreso mensual líquido declarado"
else:
    ingreso_usado = sueldo_recomendado
    ingreso_label = f"el sueldo estimado recomendado (**~${sueldo_recomendado:,.0f} CLP**)"

caprate = dividendo_clp / ingreso_usado * 100

st.metric("📊 CAPRATE (Dividendo / Ingreso mensual)", f"{caprate:.2f} %")

st.markdown(
    f"""
    <div style="background-color:#f0f4f8; border-left: 4px solid #2E86C1; padding: 10px; margin-top: 10px; border-radius: 5px;">
    <strong>¿Qué es este CAPRATE?</strong><br>
    Es el porcentaje que representa el dividendo mensual del crédito hipotecario respecto a <b>{ingreso_label}</b>.<br>
    Sirve para medir qué tanto afecta el crédito a tu capacidad de pago mensual.<br>
    Un CAPRATE menor al 25% es considerado saludable por la mayoría de las entidades financieras.<br>
    {"<br><i>Si no ingresaste tu ingreso mensual líquido, usamos el sueldo estimado recomendado calculado automáticamente para que el dividendo sea el 25% del ingreso.</i>" if ingreso_real == 0 else ""}
    </div>
    """,
    unsafe_allow_html=True
)

# Mensaje especial si el ingreso declarado es menor al recomendado
if ingreso_real > 0 and ingreso_real < sueldo_recomendado:
    st.warning(
        f"⚠️ Tu ingreso mensual líquido declarado (**~${ingreso_real:,.0f} CLP**) es menor al sueldo estimado recomendado "
        f"(**~${sueldo_recomendado:,.0f} CLP**) para este crédito. Evalúa ajustar el monto del crédito, aumentar el pie inicial o considerar plazos más largos para mejorar la viabilidad financiera."
    )

# Evaluación de viabilidad (usa ingreso real o recomendado)
st.markdown("### 🏠 Evaluación rápida de viabilidad")
if caprate <= 25 and pie_uf / precio_uf >= 0.2:
    st.success(
        f"✅ Viable: El dividendo estimado es {dividendo_clp:,.0f} CLP, "
        f"que es un {caprate:.1f}% de {ingreso_label} "
        f"(**~${ingreso_usado:,.0f} CLP**). "
        f"El sueldo estimado recomendado para este crédito es **~${sueldo_recomendado:,.0f} CLP**. "
        f"Además, el pie cubre un {pie_uf/precio_uf:.1%} del precio, lo que es saludable."
    )
elif caprate > 25 and pie_uf / precio_uf < 0.2:
    st.warning(
        f"⚠️ Riesgo alto: El dividendo mensual representa un {caprate:.1f}% de {ingreso_label} "
        f"(**~${ingreso_usado:,.0f} CLP**). "
        f"El sueldo estimado recomendado para este crédito es **~${sueldo_recomendado:,.0f} CLP**. "
        f"El pie inicial es menor al 20% recomendado. Considera aumentar el pie o reducir el monto del crédito."
    )
elif caprate > 25:
    st.warning(
        f"⚠️ Cuidado: El dividendo mensual representa un {caprate:.1f}% de {ingreso_label} "
        f"(**~${ingreso_usado:,.0f} CLP**), lo que supera el 25% recomendado para evitar riesgo financiero. "
        f"El sueldo estimado recomendado para este crédito es **~${sueldo_recomendado:,.0f} CLP**."
    )
else:
    st.info(
        f"ℹ️ El pie cubre solo un {pie_uf/precio_uf:.1%} del precio total, considera aumentarlo para reducir el crédito y las cuotas."
    )
    st.markdown(
        f"💡 El sueldo estimado recomendado para este crédito es: **~${sueldo_recomendado:,.0f} CLP** "
        f"(este valor se calcula automáticamente para que el dividendo mensual no supere el 25% del ingreso)."
    )
