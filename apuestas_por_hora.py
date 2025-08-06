import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import re
from datetime import datetime

st.set_page_config(page_title="Análisis de Apuestas - Horas y Días", layout="wide")
st.title("Análisis de Apuestas por Hora y por Día de la Semana")

uploaded_file = st.file_uploader("Subí el archivo Excel del casino", type=[".xls", ".xlsx"])
if uploaded_file:
    df = pd.read_excel(uploaded_file)
    df.columns = df.columns.str.lower().str.normalize('NFKD') \
                   .str.encode('ascii', errors='ignore').str.decode('utf-8')

    if 'id' not in df.columns:
        st.error("No se encontró una columna llamada 'ID'")
    else:
        # Extraer fecha y hora
        def parse_id(valor):
            m = re.search(r'^[0-9]{3}-(\d{4})-(\d{1,2})-(\d{1,2})-(\d{1,2})$', str(valor))
            if not m:
                return None, None
            y, mo, d, h = map(int, m.groups())
            return datetime(y, mo, d), h

        df[['fecha', 'hora_dia']] = df['id'].apply(lambda x: pd.Series(parse_id(x)))
        df = df.dropna(subset=['fecha', 'hora_dia'])

        # Mapeo de día de la semana
        dias_map = {0: 'lunes', 1: 'martes', 2: 'miércoles', 3: 'jueves',
                    4: 'viernes', 5: 'sábado', 6: 'domingo'}
        df['dia_semana'] = df['fecha'].dt.weekday.map(dias_map)

        # Columnas de texto
        cols_ap = [c for c in df.columns if 'numero de apuestas' in c]
        cols_mo = [c for c in df.columns if c.startswith('monto apostado')]
        df['cantidad_apuestas'] = df[cols_ap].sum(axis=1)
        df['monto_apostado'] = df[cols_mo].sum(axis=1) if cols_mo else 0

        # Resumen por hora
        resumen_hora = df.groupby('hora_dia').agg({
            'cantidad_apuestas':'sum',
            'monto_apostado':'sum'
        }).reset_index().sort_values('hora_dia')
        st.subheader("📅 Apuestas por Hora del Día")
        fig1, ax1 = plt.subplots(figsize=(12,5))
        sns.barplot(data=resumen_hora, x='hora_dia', y='cantidad_apuestas',
                    palette='Blues_d', ax=ax1)
        ax1.set_title("Cantidad de apuestas por hora")
        ax1.set_xlabel("Hora")
        ax1.set_ylabel("Cantidad de apuestas")
        st.pyplot(fig1)

        # Resumen por día
        resumen_dia = df.groupby('dia_semana').agg({
            'cantidad_apuestas':'sum',
            'monto_apostado':'sum'
        }).reindex(['lunes','martes','miércoles','jueves','viernes','sábado','domingo']) \
          .reset_index()

        st.subheader("📅 Apuestas por Día de la Semana")
        fig2, ax2 = plt.subplots(figsize=(10,4))
        sns.barplot(data=resumen_dia, x='dia_semana', y='cantidad_apuestas',
                    palette='Oranges_d', ax=ax2)
        ax2.set_title("Cantidad de apuestas por día de la semana")
        ax2.set_xlabel("Día")
        ax2.set_ylabel("Cantidad de apuestas")
        st.pyplot(fig2)

        # Ranking de días completo
        ranking_dia = resumen_dia.sort_values('cantidad_apuestas', ascending=False).reset_index(drop=True)
        ranking_dia['posición'] = ranking_dia.index + 1
        ranking_dia = ranking_dia[['posición','dia_semana','cantidad_apuestas','monto_apostado']]
        ranking_dia.columns = ['N°','Día','Cantidad de apuestas','Importe apostado']

        st.subheader("📊 Ranking de días por actividad")
        st.dataframe(ranking_dia.style.format({
            'Cantidad de apuestas':'{:,}',
            'Importe apostado':'${:,.2f}'
        }))
