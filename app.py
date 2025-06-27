# ... [Todo el código anterior intacto hasta después del gráfico de barras] ...

        # Diagnóstico Financiero Inteligente
        st.subheader("💡 Diagnóstico Financiero Inteligente")

        diagnosticos = []

        # Evaluación de la tasa
        if tasa_anual < 0.035:
            diagnosticos.append("🔵 Excelente tasa. Lograste condiciones muy competitivas.")
        elif tasa_anual <= 0.045:
            diagnosticos.append("🟢 Buena tasa. Estás dentro del rango óptimo actual.")
        elif tasa_anual <= 0.055:
            diagnosticos.append("🟡 Tasa aceptable, pero podrías buscar mejores opciones.")
        else:
            diagnosticos.append("🔴 Tasa alta. Evalúa cotizar con otros bancos o espera mejores condiciones.")

        # Evaluación del pie
        pie_pct = pie_uf / precio_uf
        if pie_pct >= 0.25:
            diagnosticos.append("🔵 Excelente pie inicial. Reduciste el monto y los intereses del crédito.")
        elif pie_pct >= 0.20:
            diagnosticos.append("🟢 Buen pie inicial. Cumples con lo recomendado por la banca.")
        elif pie_pct >= 0.15:
            diagnosticos.append("🟡 Pie aceptable. Considera aumentarlo si puedes.")
        else:
            diagnosticos.append("🔴 Pie muy bajo. Podrías enfrentar mayores intereses y restricciones.")

        # Evaluación del plazo
        if plazo > 25:
            diagnosticos.append("🟡 Plazo largo. Cuotas más bajas, pero pagas más intereses.")
        elif plazo < 15:
            diagnosticos.append("🟢 Plazo corto. Ahorro en intereses, pero cuota más exigente.")

        # Evaluación del costo total
        ratio_total = monto_total_uf / credito_uf
        if ratio_total > 2.0:
            diagnosticos.append("🔴 Estás pagando más del doble del crédito en total. Revisa la tasa y plazo.")
        elif ratio_total > 1.7:
            diagnosticos.append("🟡 Costo total elevado. Ajustar plazo o tasa podría ayudar.")
        else:
            diagnosticos.append("🟢 Costo total razonable. Bien controlado.")

        # Recomendación con sueldo estimado
        if sueldo_recomendado > 2_000_000:
            diagnosticos.append("🟡 El dividendo requiere un ingreso mensual alto. Evalúa reducir el monto del crédito o aumentar el pie.")
        elif sueldo_recomendado < 1_200_000:
            diagnosticos.append("🟢 Buena relación cuota / ingreso estimado. Deberías poder cumplir con holgura.")

        # Mostrar diagnósticos
        for d in diagnosticos:
            st.markdown(f"- {d}")

# --- Modo Inversionista y Recomendador (borradores) ---
elif modo == "Inversionista":
    st.info("🔧 Modo Inversionista aún en desarrollo. Próximamente podrás simular arriendo vs dividendo.")
else:
    st.info("🧠 Modo Inteligente en construcción. Pronto te ayudará a encontrar el mejor escenario según tus metas.")
