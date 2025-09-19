import streamlit as st
import pandas as pd
import altair as alt
import plotly.express as px
import os

st.set_page_config(
    page_title="Análise de Balança Comercial",
    layout="wide"
)

st.title("Balança Comercial de Santa Catarina")

# Caminho para os arquivos pré-processados
DATA_FOLDER = "pre_processed_data"

# Nomes dos arquivos
EXP_PRODUCTS_FILE = "exp_products_{}.parquet"
IMP_PRODUCTS_FILE = "imp_products_{}.parquet"
EXP_COUNTRIES_FILE = "exp_countries_{}.parquet"
IMP_COUNTRIES_FILE = "imp_countries_{}.parquet"

# --- 1. Filtros ---
col1, col2 = st.columns(2)

with col1:
    # A UF não pode ser filtrada por estado no app, já que o pré-processamento foi feito para SC
    st.info("A análise de dados pré-processados está limitada à UF de SC.")
    
with col2:
    all_years = [2024, 2023]
    selected_year = st.selectbox(
        "Selecione o Ano",
        options=all_years,
        index=0
    )

# --- 2. Cards de resumo ---
st.markdown("---")
# Você precisará pré-processar e salvar esses valores também
# Para este exemplo, vamos colocar valores fixos ou carregar de um arquivo
# (Recomendado: pré-processar e salvar em um JSON)
total_exp = 11677214409.00
total_imp = 33771587792.00
balanca_comercial = total_exp - total_imp

def format_currency_br(value):
    return f"US$ {value:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")

col3, col4, col5 = st.columns(3)
with col3:
    st.metric(label=f"Total de Exportações ({selected_year})", value=format_currency_br(total_exp))
with col4:
    st.metric(label=f"Total de Importações ({selected_year})", value=format_currency_br(total_imp))
with col5:
    st.metric(label=f"Resultado da Balança Comercial ({selected_year})", value=format_currency_br(balanca_comercial))

# ---
## Tarefa 1: Análise de Produtos e Países por Fluxo
# ---
st.markdown("---")
col6, col7 = st.columns(2)

# Carregando dados pré-processados
df_exp_products = pd.read_parquet(os.path.join(DATA_FOLDER, EXP_PRODUCTS_FILE.format(selected_year)))
df_imp_products = pd.read_parquet(os.path.join(DATA_FOLDER, IMP_PRODUCTS_FILE.format(selected_year)))

with col6:
    st.subheader("TAREFA 1 - Produtos Mais Exportados")
    num_products_exp = st.slider("Número de produtos a exibir", min_value=0, max_value=20, value=5, key='slider_exp')
    df_chart_exp = df_exp_products.nlargest(num_products_exp, 'VL_FOB')

    chart_exp = alt.Chart(df_chart_exp).mark_bar().encode(
        x=alt.X('CO_NCM', title='Código NCM', sort='-y'),
        y=alt.Y('VL_FOB', title='Valor FOB (US$)')
    ).properties(title=f'{num_products_exp} Produtos Mais Exportados ({selected_year})')
    st.altair_chart(chart_exp, use_container_width=True)
    st.dataframe(df_chart_exp, hide_index=True)

with col7:
    st.subheader("Produtos Mais Importados")
    num_products_imp = st.slider("Número de produtos a exibir", min_value=0, max_value=20, value=5, key='slider_imp')
    df_chart_imp = df_imp_products.nlargest(num_products_imp, 'VL_FOB')

    chart_imp = alt.Chart(df_chart_imp).mark_bar(color='#E57F84').encode(
        x=alt.X('CO_NCM', title='Código NCM', sort='-y'),
        y=alt.Y('VL_FOB', title='Valor FOB (US$)')
    ).properties(title=f'{num_products_imp} Produtos Mais Importados ({selected_year})')
    st.altair_chart(chart_imp, use_container_width=True)
    st.dataframe(df_chart_imp, hide_index=True)
