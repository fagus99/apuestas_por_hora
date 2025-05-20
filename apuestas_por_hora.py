import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import re
from datetime import datetime
import openai

st.set_page_config(page_title="Análisis por Hora - Casino", layout="wide")
st.title("Análisis de Apuestas por Hora (General por Horario)")

uploaded_file = st.file_uploader("Subí el archivo Excel del casino", type=[".xls", ".xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    
    # Normalizar encabezados: sin mayúsculas, sin acentos
    df.columns = df.columns.str.lower().str.normalize('NFKD').str.encode('ascii', errors='ignore').str.decode('utf-8')

    # Verificar existencia de columna 'id'
    if 'id' not in df.columns:
        st.error("No se encontró una columna llamada 'ID'")
    else:
        # Extraer fecha y hora desde columna 'ID'
        def extraer_hora_numero(valor):
            try:
                match = re.search(r"-([0-9]{4})-([0-9]{1,2})-([0-9]{1,2})-([0-9]{1,2})$", str(valor))
                if match:
                    return int(match.group(4))  # Solo la hora como número
            except:
                return None

        df['hora_dia'] = df['id'].apply(extraer_hora_numero)
        df = df.dropna(subset=['hora_dia'])

        # Detectar columnas de apuestas y montos
        columnas_apuestas = [col for col in df.columns if 'numero de apuestas' in col]
        columnas_montos = [col for col in df.columns if col.startswith('monto apostado')]

        if not columnas_apuestas:
            st.error("No se encontraron columnas de cantidad de apuestas válidas.")
        else:
            df['cantidad_apuestas'] = df[columnas_apuestas].sum(axis=1)
            df['monto_apostado'] = df[columnas_montos].sum(axis=1) if columnas_montos else 0

            resumen = df.groupby('hora_dia').agg({
                'cantidad_apuestas': 'sum',
                'monto_apostado': 'sum'
            }).reset_index().sort_values('hora_dia')

            # Gráfico: Cantidad de apuestas por hora
            st.subheader("Cantidad total de apuestas por hora del día")
            fig1, ax1 = plt.subplots(figsize=(12, 5))
            sns.barplot(data=resumen, x='hora_dia', y='cantidad_apuestas', palette='Blues_d', ax=ax1)
            ax1.set_title("Cantidad de apuestas por hora")
            ax1.set_xlabel("Hora del día")
            ax1.set_ylabel("Cantidad de apuestas")
            st.pyplot(fig1)

            # Gráfico: Monto apostado por hora
            st.subheader("Monto total apostado por hora del día")
            fig2, ax2 = plt.subplots(figsize=(12, 5))
            sns.barplot(data=resumen, x='hora_dia', y='monto_apostado', palette='Greens_d', ax=ax2)
            ax2.set_title("Monto apostado por hora")
            ax2.set_xlabel("Hora del día")
            ax2.set_ylabel("Monto apostado")
            st.pyplot(fig2)

            # Top 5 horas con más y menos apuestas
            mejores = resumen.sort_values('cantidad_apuestas', ascending=False).head(5)
            peores = resumen.sort_values('cantidad_apuestas').head(5)

            st.subheader("Top 5 horas con más apuestas")
            st.dataframe(mejores)

            st.subheader("Top 5 horas con menos apuestas")
            st.dataframe(peores)

            # IA opcional
            if st.checkbox("Generar resumen con IA"):
                try:
                    openai.api_key = st.secrets["OPENAI_API_KEY"]
                    prompt = f"""
                    Realizá un análisis de comportamiento horario de los jugadores según los datos de apuestas:
                    Mejores horas:
                    {mejores.to_string(index=False)}

                    Peores horas:
                    {peores.to_string(index=False)}

                    Considerá hábitos típicos de usuarios online y posibles razones de variación.
                    """
                    response = openai.ChatCompletion.create(
                        model="gpt-4",
                        messages=[{"role": "user", "content": prompt}]
                    )
                    st.subheader("Resumen generado con IA")
                    st.write(response.choices[0].message.content)
                except Exception as e:
                    st.warning("No se pudo generar resumen con IA. Verificá tu clave API.")
