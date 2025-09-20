import streamlit as st
import pandas as pd
import altair as alt
import plotly.express as px

st.set_page_config(
    page_title="Análise de Balança Comercial - SC 2024",
    layout="wide"
)

st.title("Balança Comercial de Santa Catarina - 2024")

# URLs dos arquivos no Hugging Face
URL_EXP = "https://huggingface.co/datasets/bruceeconomista/balanca-comercial-sc-v2-dados/resolve/main/exp_sc_2024.parquet"
URL_IMP = "https://huggingface.co/datasets/bruceeconomista/balanca-comercial-sc-v2-dados/resolve/main/imp_sc_2024.parquet"

@st.cache_data
def load_data():
    """Carrega os dados dos arquivos Parquet do Hugging Face."""
    try:
        df_exp = pd.read_parquet(URL_EXP)
        df_imp = pd.read_parquet(URL_IMP)
        
        # Limpar os nomes das colunas e garantir que a codificação está correta (o parquet já resolve a maioria)
        df_exp.columns = [col.replace('ï»¿', '') for col in df_exp.columns]
        df_imp.columns = [col.replace('ï»¿', '') for col in df_imp.columns]

        return df_exp, df_imp
    except Exception as e:
        st.error(f"Erro ao carregar os dados do Hugging Face: {e}")
        return pd.DataFrame(), pd.DataFrame()

df_exp, df_imp = load_data()

if df_exp.empty or df_imp.empty:
    st.stop()

# --- 1. Cards de resumo ---
st.markdown("---")
col1, col2, col3 = st.columns(3)

# Cálculo dos totais (os dataframes já estão filtrados para SC e 2024)
total_exp = df_exp['VL_FOB'].sum()
total_imp = df_imp['VL_FOB'].sum()
balanca_comercial = total_exp - total_imp
selected_year = 2024

# Funções de formatação
def format_brl(value, decimals=2):
    return f"{value:,.{decimals}f}".replace(",", "X").replace(".", ",").replace("X", ".")

def format_currency_br(value):
    # Formata sem casas decimais, mas com separador de milhar
    return f"US$ {format_brl(value, 0)}"

with col1:
    st.metric(
        label=f"Total de Exportações ({selected_year})",
        value=format_currency_br(total_exp)
    )

with col2:
    st.metric(
        label=f"Total de Importações ({selected_year})",
        value=format_currency_br(total_imp)
    )
    
with col3:
    st.metric(
        label=f"Resultado da Balança Comercial ({selected_year})",
        value=format_currency_br(balanca_comercial)
    )

# ---
## Análise de Produtos e Países por Fluxo
# ---
# --- 2. Análise Gráfica (Produtos) ---
st.markdown("---")
col4, col5 = st.columns(2)

def format_value(value):
    if value >= 1_000_000_000:
        return f"{value / 1_000_000_000:.1f}B"
    if value >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    return str(value)

with col4:
    st.subheader("Produtos Mais Exportados")
    num_products_exp = st.slider(
        "Número de produtos a exibir", min_value=1, max_value=20, value=5, key='slider_exp'
    )
    
    df_chart_exp = df_exp.groupby(['CO_NCM', 'NO_NCM_POR']).agg(
        VL_FOB=('VL_FOB', 'sum'),
        KG_LIQUIDO=('KG_LIQUIDO', 'sum')
    ).nlargest(num_products_exp, 'VL_FOB').reset_index()

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
        df_exp_display = df_chart_exp.rename(columns={
            'CO_NCM': 'NCM',
            'NO_NCM_POR': 'Produto',
            'VL_FOB': 'Valor FOB',
            'KG_LIQUIDO': 'Total KG'
        })
        
        st.subheader(f"Dados dos {num_products_exp} Produtos Mais Exportados")
        st.dataframe(
            df_exp_display[['NCM', 'Produto', 'Valor FOB', 'Total KG']].style.format({
                'Valor FOB': lambda x: format_brl(x, 2),
                'Total KG': lambda x: format_brl(x, 0),
            }),
            use_container_width=True,
            hide_index=True
        )

with col5:
    st.subheader("Produtos Mais Importados")
    num_products_imp = st.slider(
        "Número de produtos a exibir", min_value=1, max_value=20, value=5, key='slider_imp'
    )

    df_chart_imp = df_imp.groupby(['CO_NCM', 'NO_NCM_POR']).agg(
        VL_FOB=('VL_FOB', 'sum'),
        KG_LIQUIDO=('KG_LIQUIDO', 'sum')
    ).nlargest(num_products_imp, 'VL_FOB').reset_index()
    
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
        df_imp_display = df_chart_imp.rename(columns={
            'CO_NCM': 'NCM',
            'NO_NCM_POR': 'Produto',
            'VL_FOB': 'Valor FOB',
            'KG_LIQUIDO': 'Total KG'
        })
        
        st.subheader(f"Dados dos {num_products_imp} Produtos Mais Importados")
        st.dataframe(
            df_imp_display[['NCM', 'Produto', 'Valor FOB', 'Total KG']].style.format({
                'Valor FOB': lambda x: format_brl(x, 2),
                'Total KG': lambda x: format_brl(x, 0),
            }),
            use_container_width=True,
            hide_index=True
        )

# --- 3. Treemaps de Países por Produto Selecionado ---
st.markdown("---")
st.header("Fluxo de Exportação e Importação por País (Principais Produtos)")
col6, col7 = st.columns(2)

# Filtrar o DataFrame por produtos selecionados antes de agrupar para o treemap
df_exp_filtered_products = df_exp[df_exp['NO_NCM_POR'].isin(top_exp_products)]
df_imp_filtered_products = df_imp[df_imp['NO_NCM_POR'].isin(top_imp_products)]

with col6:
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
            title=f'Distribuição de Exportações por País',
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

with col7:
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
            title='Distribuição de Importações por País',
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
