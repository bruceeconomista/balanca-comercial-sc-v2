import streamlit as st
import pandas as pd
import altair as alt
import plotly.express as px
import os
import json

st.set_page_config(
    page_title="Análise de Balança Comercial",
    layout="wide"
)

st.title("Balança Comercial de Santa Catarina")

# Nomes dos arquivos
DATA_FOLDER = "pre_processed_data"

# Nomes dos arquivos de dados pré-processados
EXP_PRODUCTS_FILE = "exp_products_{}.parquet"
IMP_PRODUCTS_FILE = "imp_products_{}.parquet"
EXP_COUNTRIES_FILE = "exp_countries_{}.parquet"
IMP_COUNTRIES_FILE = "imp_countries_{}.parquet"
EXP_TOTAL_FILE = "exp_total_{}.json"
IMP_TOTAL_FILE = "imp_total_{}.json"

# --- 1. Filtros ---
col1, col2 = st.columns(2)

with col1:
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

# Carregando dados totais de arquivos JSON para performance
exp_total_path = os.path.join(DATA_FOLDER, EXP_TOTAL_FILE.format(selected_year))
imp_total_path = os.path.join(DATA_FOLDER, IMP_TOTAL_FILE.format(selected_year))

try:
    with open(exp_total_path, 'r') as f:
        total_exp = json.load(f)['VL_FOB']
    with open(imp_total_path, 'r') as f:
        total_imp = json.load(f)['VL_FOB']
except FileNotFoundError:
    st.error(f"Erro: Arquivos de totais para o ano {selected_year} não encontrados.")
    total_exp = 0
    total_imp = 0

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

# Carregando dados pré-processados
try:
    df_exp_products = pd.read_parquet(os.path.join(DATA_FOLDER, EXP_PRODUCTS_FILE.format(selected_year)))
    df_imp_products = pd.read_parquet(os.path.join(DATA_FOLDER, IMP_PRODUCTS_FILE.format(selected_year)))
    df_exp_countries = pd.read_parquet(os.path.join(DATA_FOLDER, EXP_COUNTRIES_FILE.format(selected_year)))
    df_imp_countries = pd.read_parquet(os.path.join(DATA_FOLDER, IMP_COUNTRIES_FILE.format(selected_year)))

except FileNotFoundError:
    st.error("Erro: Os arquivos .parquet não foram encontrados. Certifique-se de que estão na pasta 'pre_processed_data'.")
    df_exp_products = pd.DataFrame()
    df_imp_products = pd.DataFrame()
    df_exp_countries = pd.DataFrame()
    df_imp_countries = pd.DataFrame()

# ---
## Tarefa 1: Análise de Produtos e Países por Fluxo
# ---
st.markdown("---")
col6, col7 = st.columns(2)

def format_value(value):
    if value >= 1_000_000_000:
        return f"{value / 1_000_000_000:.1f}B"
    if value >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    return str(value)

def format_brl(value, decimals=2):
    return f"{value:,.{decimals}f}".replace(",", "X").replace(".", ",").replace("X", ".")

with col6:
    st.subheader("TAREFA 1 - Produtos Mais Exportados")
    num_products_exp = st.slider(
        "Número de produtos a exibir", min_value=0, max_value=20, value=5, key='slider_exp'
    )
    
    df_chart_exp = df_exp_products.nlargest(num_products_exp, 'VL_FOB').reset_index()

    df_chart_exp['VL_FOB_FORMATADO'] = df_chart_exp['VL_FOB'].apply(format_value)

    chart_exp = alt.Chart(df_chart_exp).mark_bar().encode(
        x=alt.X('CO_NCM:N', title='Código NCM', sort='-y'),
        y=alt.Y('VL_FOB', title='Valor FOB (US$)'),
        tooltip=[
            alt.Tooltip('NO_NCM_POR', title='Nome do Produto'),
            alt.Tooltip('KG_LIQUIDO', title='Total de Kg', format=',.0f'),
            alt.Tooltip('VL_FOB_FORMATADO', title='Valor FOB (US$)')
        ]
    ).properties(
        title=f'{num_products_exp} Produtos Mais Exportados ({selected_year})'
    )
    st.altair_chart(chart_exp, use_container_width=True)
    
    top_exp_products = df_chart_exp['NO_NCM_POR'].unique().tolist()
    
    if not df_chart_exp.empty:
        df_exp_pivot = df_exp_products.copy()
        
        total_fob_selected_year = df_exp_pivot['VL_FOB'].sum()
        df_exp_pivot['Participacao (%)'] = (df_exp_pivot['VL_FOB'] / total_fob_selected_year) * 100 if total_fob_selected_year > 0 else 0
        
        # Filtra apenas os produtos selecionados pelo slider
        df_exp_pivot = df_exp_pivot[df_exp_pivot['NO_NCM_POR'].isin(top_exp_products)]

        # Calcula as colunas solicitadas
        total_fob_selected_year = df_exp_pivot['VL_FOB'].sum()
        df_exp_pivot['Participacao (%)'] = (df_exp_pivot['VL_FOB'] / total_fob_selected_year) * 100 if total_fob_selected_year > 0 else 0
        
        df_exp_display = df_exp_pivot.rename(columns={
            'CO_NCM': 'NCM',
            'NO_NCM_POR': 'Produto',
            'VL_FOB': 'Valor FOB',
            'KG_LIQUIDO': 'Total KG'
        })
        
        st.subheader(f"Dados dos {num_products_exp} Produtos Mais Exportados")
        st.dataframe(
            df_exp_display[[
                'NCM', 'Produto', 'Valor FOB', 'Total KG', 'Participacao (%)'
            ]].style.format({
                'Valor FOB': lambda x: format_brl(x, 2),
                'Total KG': lambda x: format_brl(x, 0),
                'Participacao (%)': '{:.2f}%',
            }),
            use_container_width=True,
            hide_index=True
        )


with col7:
    st.subheader("Produtos Mais Importados")
    num_products_imp = st.slider(
        "Número de produtos a exibir", min_value=0, max_value=20, value=5, key='slider_imp'
    )

    df_chart_imp = df_imp_products.nlargest(num_products_imp, 'VL_FOB').reset_index()
    
    df_chart_imp['VL_FOB_FORMATADO'] = df_chart_imp['VL_FOB'].apply(format_value)
    
    chart_imp = alt.Chart(df_chart_imp).mark_bar(color='#E57F84').encode(
        x=alt.X('CO_NCM:N', title='Código NCM', sort='-y'),
        y=alt.Y('VL_FOB', title='Valor FOB (US$)'),
        tooltip=[
            alt.Tooltip('NO_NCM_POR', title='Nome do Produto'),
            alt.Tooltip('KG_LIQUIDO', title='Total de Kg', format=',.0f'),
            alt.Tooltip('VL_FOB_FORMATADO', title='Valor FOB (US$)')
        ]
    ).properties(
        title=f'{num_products_imp} Produtos Mais Importados ({selected_year})'
    )
    st.altair_chart(chart_imp, use_container_width=True)
    
    top_imp_products = df_chart_imp['NO_NCM_POR'].unique().tolist()
    
    if not df_chart_imp.empty:
        df_imp_pivot = df_imp_products.copy()
        
        total_fob_selected_year = df_imp_pivot['VL_FOB'].sum()
        df_imp_pivot['Participacao (%)'] = (df_imp_pivot['VL_FOB'] / total_fob_selected_year) * 100 if total_fob_selected_year > 0 else 0
        
        df_imp_pivot = df_imp_pivot[df_imp_pivot['NO_NCM_POR'].isin(top_imp_products)]
        
        df_imp_display = df_imp_pivot.rename(columns={
            'CO_NCM': 'NCM',
            'NO_NCM_POR': 'Produto',
            'VL_FOB': 'Valor FOB',
            'KG_LIQUIDO': 'Total KG'
        })
        
        st.subheader(f"Dados dos {num_products_imp} Produtos Mais Importados")
        st.dataframe(
            df_imp_display[[
                'NCM', 'Produto', 'Valor FOB', 'Total KG', 'Participacao (%)'
            ]].style.format({
                'Valor FOB': lambda x: format_brl(x, 2),
                'Total KG': lambda x: format_brl(x, 0),
                'Participacao (%)': '{:.2f}%',
            }),
            use_container_width=True,
            hide_index=True
        )


# --- 4. Treemaps de Países por Produto Selecionado ---
st.markdown("---")
st.header("TAREFA 1 - Fluxo de Exportação e Importação por País (Principais Produtos)")
col8, col9 = st.columns(2)

df_exp_filtered_products = df_exp_countries
df_imp_filtered_products = df_imp_countries

with col8:
    st.subheader("Exportações dos Principais Produtos por País")
    
    total_exp_sc = df_exp_filtered_products['VL_FOB'].sum()
    df_treemap_exp = df_exp_filtered_products.groupby('NO_PAIS').agg(
        VL_FOB=('VL_FOB', 'sum'),
        KG_LIQUIDO=('KG_LIQUIDO', 'sum')
    ).reset_index()

    if total_exp_sc > 0:
        df_treemap_exp['Participacao (%)'] = (df_treemap_exp['VL_FOB'] / total_exp_sc) * 100
        fig_exp = px.treemap(
            df_treemap_exp,
            path=['NO_PAIS'],
            values='VL_FOB',
            title=f'Distribuição de Exportações por País ({selected_year})',
            color_discrete_sequence=px.colors.qualitative.Pastel,
            hover_name='NO_PAIS',
            hover_data={
                'VL_FOB': ':,2f',
                'KG_LIQUIDO': ':,0f',
                'Participacao (%)': ':.2f'
            }
        )
        st.plotly_chart(fig_exp, use_container_width=True)
    else:
        st.info("Não há dados de exportação para a seleção atual.")

with col9:
    st.subheader("Importações dos Principais Produtos por País")

    total_imp_sc = df_imp_filtered_products['VL_FOB'].sum()
    df_treemap_imp = df_imp_filtered_products.groupby('NO_PAIS').agg(
        VL_FOB=('VL_FOB', 'sum'),
        KG_LIQUIDO=('KG_LIQUIDO', 'sum')
    ).reset_index()

    if total_imp_sc > 0:
        df_treemap_imp['Participacao (%)'] = (df_treemap_imp['VL_FOB'] / total_imp_sc) * 100
        fig_imp = px.treemap(
            df_treemap_imp,
            path=['NO_PAIS'],
            values='VL_FOB',
            title=f'Distribuição de Importações por País ({selected_year})',
            color_discrete_sequence=px.colors.qualitative.Pastel,
            hover_name='NO_PAIS',
            hover_data={
                'VL_FOB': ':,2f',
                'KG_LIQUIDO': ':,0f',
                'Participacao (%)': ':.2f'
            }
        )
        st.plotly_chart(fig_imp, use_container_width=True)
    else:
        st.info("Não há dados de importação para a seleção atual.")
