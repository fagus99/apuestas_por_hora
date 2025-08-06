import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import re
from datetime import datetime

st.set_page_config(page_title="Análisis de Apuestas por Hora y Día", layout="wide")
st.title("Análisis de Apuestas por Hora y por Día de la Semana")

uploaded_file = st.file_uploader("Subí tu archivo Excel del casino", type=["xlsx", "xls"])
if uploaded_file:
    df = pd.read_excel(uploaded_file)
    df.columns = df.columns.str.lower().str.normalize('NFKD')\
                   .str.encode('ascii', errors='ignore').str.decode('utf-8')

    # Extraer hora y fecha desde ID
    def parse_id(v):
        m = re.search(r"^[0-9]{3}-(\d{4})-(\d{1,2})-(\d{1,2})-(\d{1,2})$", str(v))
        if not m:
            return None, None
        year, mo, day, hr = map(int, m.groups())
        return datetime(year, mo, day), hr

    df[['fecha', 'hora_dia']] = df['id'].apply(lambda x: pd.Series(parse_id(x)))
    df = df.dropna(subset=['fecha', 'hora_dia'])

    # Calcular día de la semana en español
    # Para compatibilidad, no dependemos del locale: usamos weekday() + mapping manual
    dias = {0: 'lunes', 1: 'martes', 2: 'miércoles', 3: 'jueves',
            4: 'viernes', 5: 'sábado', 6: 'domingo'}
    df['dia_semana'] = df['fecha'].dt.weekday.map(dias)

    # Columnas apuestas y montos como antes
    cols_ap = [c for c in df.columns if 'numero de apuestas' in c]
    cols_mo = [c for c in df.columns if c.startswith('monto apostado')]
    df['cantidad_apuestas'] = df[cols_ap].sum(axis=1)
    df['monto_apostado'] = df[cols_mo].sum(axis=1) if cols_mo else 0

    # Agrupar por hora
    resumen_hora = df.groupby('hora_dia').agg({'cantidad_apuestas':'sum','monto_apostado':'sum'})\
                      .reset_index().sort_values('hora_dia')

    st.subheader("🔹 Apuestas por Hora del Día")
    fig1, ax1 = plt.subplots(figsize=(12,5))
    sns.barplot(data=resumen_hora, x='hora_dia', y='cantidad_apuestas',
                palette='Blues_d', ax=ax1)
    ax1.set_title("Cantidad de apuestas por hora")
    ax1.set_xlabel("Hora del día")
    ax1.set_ylabel("Cantidad de apuestas")
    st.pyplot(fig1)

    # Agrupar por día de la semana
    resumen_dia = df.groupby('dia_semana').agg({'cantidad_apuestas':'sum','monto_apostado':'sum'})\
                     .reindex(['lunes','martes','miércoles','jueves','viernes','sábado','domingo'])\
                     .reset_index()

    st.subheader("🔹 Apuestas por Día de la Semana")
    fig2, ax2 = plt.subplots(figsize=(10,4))
    sns.barplot(data=resumen_dia, x='dia_semana', y='cantidad_apuestas',
                palette='Oranges_d', ax=ax2)
    ax2.set_title("Cantidad de apuestas por día de la semana")
    ax2.set_xlabel("Día")
    ax2.set_ylabel("Cantidad de apuestas")
    st.pyplot(fig2)

    # Top 5 días con más y menos apuestas
    mejores_dias = resumen_dia.sort_values('cantidad_apuestas', ascending=False).head(5)
    peores_dias = resumen_dia.sort_values('cantidad_apuestas').head(5)

    st.subheader("📈 Top 5 días con más apuestas")
    st.dataframe(mejores_dias)

    st.subheader("📉 Top 5 días con menos apuestas")
    st.dataframe(peores_dias)
