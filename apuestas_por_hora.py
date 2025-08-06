import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import re
from datetime import datetime

st.set_page_config(page_title="Análisis de Apuestas - Horas y Días", layout="wide")
st.title("Análisis de Apuestas: por Hora, Día y Top 5")

uploaded_file = st.file_uploader("Subí el archivo Excel del casino", type=[".xls", ".xlsx"])
if uploaded_file:
    df = pd.read_excel(uploaded_file)
    df.columns = df.columns.str.lower().str.normalize('NFKD') \
                   .str.encode('ascii', errors='ignore').str.decode('utf-8')

    if 'id' not in df.columns:
        st.error("No se encontró una columna llamada 'id'")
    else:
        def parse_id(valor):
            m = re.search(r'^[0-9]{3}-(\d{4})-(\d{1,2})-(\d{1,2})-(\d{1,2})$', str(valor))
            if not m:
                return None, None
            y, mo, d, hr = map(int, m.groups())
            return datetime(y, mo, d), hr

        df[['fecha', 'hora_dia']] = df['id'].apply(lambda x: pd.Series(parse_id(x)))
        df = df.dropna(subset=['fecha', 'hora_dia'])

        dias_map = {0:'lunes',1:'martes',2:'miércoles',3:'jueves',
                    4:'viernes',5:'sábado',6:'domingo'}
        df['dia_semana'] = df['fecha'].dt.weekday.map(dias_map)

        cols_ap = [c for c in df.columns if 'numero de apuestas' in c]
        cols_mo = [c for c in df.columns if c.startswith('monto apostado')]
        df['cantidad_apuestas'] = df[cols_ap].sum(axis=1)
        df['monto_apostado'] = df[cols_mo].sum(axis=1) if cols_mo else 0

        resumen_hora = df.groupby('hora_dia').agg({
            'cantidad_apuestas':'sum','monto_apostado':'sum'
        }).reset_index().sort_values('hora_dia')

        st.subheader("📅 Apuestas por Hora del Día")
        fig1, ax1 = plt.subplots(figsize=(12,5))
        sns.barplot(data=resumen_hora, x='hora_dia', y='cantidad_apuestas',
                    palette='Blues_d', ax=ax1)
        ax1.set_title("Cantidad de apuestas por hora")
        ax1.set_xlabel("Hora")
        ax1.set_ylabel("Cantidad de apuestas")
        st.pyplot(fig1)

        resumen_dia = df.groupby('dia_semana').agg({
            'cantidad_apuestas':'sum','monto_apostado':'sum'
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

        ranking_dia = resumen_dia.sort_values('cantidad_apuestas', ascending=False).reset_index(drop=True)
        ranking_dia['posición'] = ranking_dia.index + 1
        ranking_dia = ranking_dia[['posición','dia_semana','cantidad_apuestas','monto_apostado']]
        ranking_dia.columns = ['N°','Día','Cantidad de apuestas','Importe apostado']

        st.subheader("📊 Ranking de días por actividad")
        st.dataframe(ranking_dia.style.format({
            'Cantidad de apuestas':'{:,}',
            'Importe apostado':'${:,.2f}'
        }))

        mejores_h = resumen_hora.sort_values('cantidad_apuestas', ascending=False).head(5).reset_index(drop=True)
        mejores_h['posición'] = mejores_h.index + 1
        mejores_h = mejores_h[['posición','hora_dia','cantidad_apuestas','monto_apostado']]
        mejores_h.columns = ['N°','Hora','Cantidad de apuestas','Importe apostado']

        st.subheader("⏱️ Top 5 horas con más apuestas")
        st.dataframe(mejores_h.style.format({
            'Cantidad de apuestas':'{:,}',
            'Importe apostado':'${:,.2f}'
        }))

        peores_h = resumen_hora.sort_values('cantidad_apuestas').head(5).reset_index(drop=True)
        peores_h['posición'] = peores_h.index + 1
        peores_h = peores_h[['posición','hora_dia','cantidad_apuestas','monto_apostado']]
        peores_h.columns = ['N°','Hora','Cantidad de apuestas','Importe apostado']

        st.subheader("🕑 Top 5 horas con menos apuestas")
        st.dataframe(peores_h.style.format({
            'Cantidad de apuestas':'{:,}',
            'Importe apostado':'${:,.2f}'
        }))
