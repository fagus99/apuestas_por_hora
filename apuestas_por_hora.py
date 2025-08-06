import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import re
from datetime import datetime

st.set_page_config(page_title="Análisis de Apuestas por Hora y Día", layout="wide")
st.title("🎰 Apuestas: ranking por Hora y Día de la Semana")

uploaded_file = st.file_uploader("Subí tu archivo Excel del casino", type=["xlsx","xls"])
if uploaded_file:
    df = pd.read_excel(uploaded_file)
    df.columns = df.columns.str.lower().str.normalize('NFKD')\
                   .str.encode('ascii', errors='ignore').str.decode('utf-8')

    # Parsear fecha y hora desde 'id'
    m = df['id'].str.extract(r'^[0-9]{3}-(\d{4})-(\d{1,2})-(\d{1,2})-(\d{1,2})$')
    df[['year','month','day','hour']] = m.astype(float).astype(int)
    df['fecha'] = pd.to_datetime(df[['year','month','day']])
    df = df.dropna(subset=['fecha','hour'])

    dias = {0:'lunes',1:'martes',2:'miércoles',3:'jueves',4:'viernes',5:'sábado',6:'domingo'}
    df['dia_semana'] = df['fecha'].dt.weekday.map(dias)

    # Calcular montos y conteo
    cols_ap = [c for c in df.columns if 'numero de apuestas' in c]
    cols_mo = [c for c in df.columns if c.startswith('monto apostado')]
    df['cantidad_apuestas'] = df[cols_ap].sum(axis=1)
    df['monto_apostado'] = df[cols_mo].sum(axis=1) if cols_mo else 0

    # Ranking por hora
    ranking_hora = (
        df.groupby('hour')['cantidad_apuestas']
        .sum().reset_index().sort_values('cantidad_apuestas', ascending=False)
    )

    st.subheader("📈 Ranking de horas por cantidad de apuestas")
    st.dataframe(ranking_hora.rename(columns={'hour':'Hora','cantidad_apuestas':'Apuestas'}))

    # Ranking por día de la semana
    ranking_dia = (
        df.groupby('dia_semana')['cantidad_apuestas']
        .sum().reindex(['lunes','martes','miércoles','jueves','viernes','sábado','domingo'])
        .reset_index().sort_values('cantidad_apuestas', ascending=False)
    )

    st.subheader("📈 Ranking de días por cantidad de apuestas")
    st.dataframe(ranking_dia.rename(columns={'dia_semana':'Día','cantidad_apuestas':'Apuestas'}))
