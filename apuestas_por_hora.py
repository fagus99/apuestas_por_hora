import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import re
from datetime import datetime
from io import BytesIO
import openai

st.set_page_config(page_title="Análisis por Hora - Casino", layout="wide")
st.title("Análisis de Apuestas por Hora")

uploaded_file = st.file_uploader("Subí el archivo Excel del casino", type=[".xls", ".xlsx"])

if uploaded_file:
    # Leer Excel
    df = pd.read_excel(uploaded_file)

    # Normalizar nombres de columnas
    df.columns = df.columns.str.lower().str.normalize('NFKD').str.encode('ascii', errors='ignore').str.decode('utf-8')

    # Extraer fecha y hora desde columna ID
    if 'id' not in df.columns:
        st.error("No se encontró una columna llamada 'ID'")
    else:
        def procesar_id(valor):
            try:
                partes = valor.split('-')
                if len(partes) >= 5:
                    anio = partes[-4]
                    mes = int(partes[-3])
                    dia = int(partes[-2])
                    hora = int(partes[-1])
                    fecha = f"{anio}-{mes:02}-{dia:02}"
                    return fecha, hora
            except:
                return None, None

        df[['fecha', 'hora']] = df['id'].astype(str).apply(lambda x: pd.Series(procesar_id(x)))
        df = df.dropna(subset=['fecha', 'hora'])

        # Crear datetime combinando fecha + hora
        df['fecha_hora'] = pd.to_datetime(df['fecha'] + ' ' + df['hora'].astype(int).astype(str) + ":00", format="%Y-%m-%d %H:%M")

        # Detectar columnas de apuestas y montos
        columnas_apuestas = [col for col in df.columns if 'numero de apuestas' in col]
        columnas_montos = [col for col in df.columns if col.startswith('monto apostado')]

        if not columnas_apuestas:
            st.error("No se encontraron columnas de cantidad de apuestas válidas.")
        else:
            # Agrupar por hora
            df['cantidad_apuestas'] = df[columnas_apuestas].sum(axis=1)
            df['monto_apostado'] = df[columnas_montos].sum(axis=1) if columnas_montos else 0

            resumen = df.groupby('fecha_hora').agg({
                'cantidad_apuestas': 'sum',
                'monto_apostado': 'sum'
            }).reset_index()

            # Gráfico de cantidad de apuestas
            st.subheader("Cantidad total de apuestas por hora")
            fig1, ax1 = plt.subplots(figsize=(12, 5))
            sns.lineplot(data=resumen, x='fecha_hora', y='cantidad_apuestas', ax=ax1)
            ax1.set_title("Apuestas por hora")
            ax1.set_xlabel("Hora")
            ax1.set_ylabel("Cantidad de apuestas")
            st.pyplot(fig1)

            # Gráfico de monto apostado
            st.subheader("Monto total apostado por hora")
            fig2, ax2 = plt.subplots(figsize=(12, 5))
            sns.lineplot(data=resumen, x='fecha_hora', y='monto_apostado', ax=ax2)
            ax2.set_title("Montos apostados por hora")
            ax2.set_xlabel("Hora")
            ax2.set_ylabel("Monto apostado")
            st.pyplot(fig2)

            # Mostrar mejores y peores horas
            mejores = resumen.sort_values('cantidad_apuestas', ascending=False).head(5)
            peores = resumen.sort_values('cantidad_apuestas', ascending=True).head(5)

            st.subheader("Top 5 horas con más apuestas")
            st.dataframe(mejores)

            st.subheader("Top 5 horas con menos apuestas")
            st.dataframe(peores)

            # Resumen con IA (opcional si configuras API KEY de OpenAI)
            if st.checkbox("Generar resumen con IA"):
                try:
                    openai.api_key = st.secrets["OPENAI_API_KEY"]
                    prompt = f"""
                    Generá un breve análisis del comportamiento horario de apuestas basado en estos datos:
                    Mejores horas:
                    {mejores.to_string(index=False)}

                    Peores horas:
                    {peores.to_string(index=False)}

                    Considerá hábitos de los jugadores y posibles causas.
                    """
                    response = openai.ChatCompletion.create(
                        model="gpt-4",
                        messages=[{"role": "user", "content": prompt}]
                    )
                    st.subheader("Resumen generado con IA")
                    st.write(response.choices[0].message.content)
                except Exception as e:
                    st.warning("No se pudo generar resumen con IA. Verificá tu clave API de OpenAI.")
