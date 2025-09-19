import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import pydeck as pdk
import requests
import json
from PIL import Image

# Configuração da página
st.set_page_config(layout="wide")

# Título e descrição
st.title("Balança Comercial de Santa Catarina")
st.markdown("Análise dos dados de importação e exportação do estado de Santa Catarina, Brasil.")

# Tentar carregar os dados
try:
    df_geral = pd.read_csv("https://raw.githubusercontent.com/bruceeconomista/balanca-comercial-sc-v2/main/balanca_comercial_sc.csv", sep=';', encoding='latin-1', skipinitialspace=True)
    st.write("Dados carregados com sucesso!")
except Exception as e:
    st.error(f"Erro ao carregar os dados: {e}")
    st.stop()

# Tentar processar os dados
try:
    df_geral['CO_ANO'] = df_geral['CO_ANO'].astype(int)
    # df_geral['DT_NCM'] = pd.to_datetime(df_geral['DT_NCM']) # Comentado para evitar erro
    df_geral['KG_LIQUIDO'] = df_geral['KG_LIQUIDO'].astype(float)
    df_geral['VL_FOB'] = df_geral['VL_FOB'].astype(float)
except Exception as e:
    st.error(f"Erro ao processar os dados: {e}")
    st.stop()

# Sidebar
st.sidebar.header("Filtros")

# Filtro de ano
ano_selecionado = st.sidebar.slider(
    "Ano",
    min_value=int(df_geral['CO_ANO'].min()),
    max_value=int(df_geral['CO_ANO'].max()),
    value=int(df_geral['CO_ANO'].min())
)

# Filtro de tipo de operação
tipo_operacao = st.sidebar.radio(
    "Tipo de Operação",
    ('Exportação', 'Importação', 'Ambos')
)

# Filtro de dados na tabela
# Tentar exibir a tabela
try:
    df_filtrado = df_geral[df_geral['CO_ANO'] == ano_selecionado]
    if tipo_operacao == 'Exportação':
        df_filtrado = df_filtrado[df_filtrado['NO_EXP'] == 'Exportação']
    elif tipo_operacao == 'Importação':
        df_filtrado = df_filtrado[df_filtrado['NO_IMP'] == 'Importação']

    st.subheader(f"Dados filtrados para o ano de {ano_selecionado}")
    st.dataframe(df_filtrado)
except Exception as e:
    st.error(f"Erro ao filtrar ou exibir a tabela: {e}")
    st.stop()


# Gráficos
st.write("---")
st.subheader("Visualizações")

# Gráfico de barras
try:
    df_barras = df_filtrado.groupby('NO_PAIS_ORIGEM').agg(
        total_fob=('VL_FOB', 'sum')
    ).reset_index().nlargest(10, 'total_fob')

    fig_barras = px.bar(
        df_barras,
        x='NO_PAIS_ORIGEM',
        y='total_fob',
        title=f"Principais Países de Origem/Destino em {ano_selecionado}"
    )
    st.plotly_chart(fig_barras, use_container_width=True)
except Exception as e:
    st.error(f"Erro ao gerar gráfico de barras: {e}")

# Gráfico de pizza
try:
    df_pizza = df_filtrado.groupby('NO_PRODUTO').agg(
        total_fob=('VL_FOB', 'sum')
    ).reset_index().nlargest(5, 'total_fob')

    fig_pizza = px.pie(
        df_pizza,
        values='total_fob',
        names='NO_PRODUTO',
        title=f"Principais Produtos em {ano_selecionado}"
    )
    st.plotly_chart(fig_pizza, use_container_width=True)
except Exception as e:
    st.error(f"Erro ao gerar gráfico de pizza: {e}")


# Mapa usando Pydeck
try:
    df_mapa = df_filtrado.groupby(['NO_PAIS_ORIGEM', 'SG_UF_NCM']).agg(
        lat=('lat', 'first'),
        lon=('lon', 'first'),
        total_fob=('VL_FOB', 'sum')
    ).reset_index()

    layer = pdk.Layer(
        'HeatmapLayer',
        data=df_mapa,
        opacity=0.9,
        get_position=['lon', 'lat'],
        threshold=0.01
    )

    view_state = pdk.ViewState(
        latitude=-27.5969,
        longitude=-48.5495,
        zoom=5,
        pitch=50
    )

    r = pdk.Deck(
        layers=[layer],
        initial_view_state=view_state,
        tooltip={"text": "{NO_PAIS_ORIGEM}\nTotal FOB: {total_fob}"}
    )

    st.pydeck_chart(r)
    st.write("Mapa gerado com sucesso!")

except Exception as e:
    st.error(f"Erro ao gerar o mapa: {e}")
