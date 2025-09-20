import streamlit as st
import pandas as pd
import altair as alt
import plotly.express as px

st.set_page_config(
    page_title="Análise de Balança Comercial - SC 2024",
    layout="wide"
)

st.title("Balança Comercial de Santa Catarina - 2024")

# URLs dos arquivos no Hugging Face (2024 e 2023)
URL_EXP_2024 = "https://huggingface.co/datasets/bruceeconomista/balanca-comercial-sc-v2-dados/resolve/main/exp_sc_2024.parquet"
URL_IMP_2024 = "https://huggingface.co/datasets/bruceeconomista/balanca-comercial-sc-v2-dados/resolve/main/imp_sc_2024.parquet"
URL_EXP_2023 = "https://huggingface.co/datasets/bruceeconomista/balanca-comercial-sc-v2-dados/resolve/main/exp_sc_2023.parquet"
URL_IMP_2023 = "https://huggingface.co/datasets/bruceeconomista/balanca-comercial-sc-v2-dados/resolve/main/imp_sc_2023.parquet"

@st.cache_data
def load_data():
    """Carrega os dados de 2024 e 2023 e calcula as variações interanuais."""
    try:
        # Carrega os dados de 2024
        df_exp_2024 = pd.read_parquet(URL_EXP_2024)
        df_imp_2024 = pd.read_parquet(URL_IMP_2024)

        # Carrega os dados de 2023
        df_exp_2023 = pd.read_parquet(URL_EXP_2023)
        df_imp_2023 = pd.read_parquet(URL_IMP_2023)

        # Trata os nomes das colunas
        df_exp_2024.columns = [col.replace('ï»¿', '') for col in df_exp_2024.columns]
        df_imp_2024.columns = [col.replace('ï»¿', '') for col in df_imp_2024.columns]
        df_exp_2023.columns = [col.replace('ï»¿', '') for col in df_exp_2023.columns]
        df_imp_2023.columns = [col.replace('ï»¿', '') for col in df_imp_2023.columns]

        return df_exp_2024, df_imp_2024, df_exp_2023, df_imp_2023
    except Exception as e:
        st.error(f"Erro ao carregar os dados do Hugging Face: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

df_exp, df_imp, df_exp_2023, df_imp_2023 = load_data()

if df_exp.empty or df_imp.empty or df_exp_2023.empty or df_imp_2023.empty:
    st.stop()

# Funções de formatação
def format_brl(value, decimals=2):
    return f"{value:,.{decimals}f}".replace(",", "X").replace(".", ",").replace("X", ".")

def format_currency_br(value):
    return f"US$ {format_brl(value, 0)}"

def format_value(value):
    if value >= 1_000_000_000:
        return f"{value / 1_000_000_000:.1f}B"
    if value >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    return str(value)

# --- 1. Cards de resumo ---
st.markdown("---")
col1, col2, col3 = st.columns(3)

# Cálculo dos totais
total_exp = df_exp['VL_FOB'].sum()
total_imp = df_imp['VL_FOB'].sum()
balanca_comercial = total_exp - total_imp
selected_year = 2024

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
st.header("Análise de Produtos e Países por Fluxo")
# --- 2. Análise Gráfica (Produtos) ---
st.markdown("---")
col4, col5 = st.columns(2)

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

# ---
st.header("Análise Geral de Parceiros Comerciais")
# --- 4. Tabelas dos Maiores Países e Treemaps Gerais ---
st.markdown("---")
col8, col9 = st.columns(2)

# Lógica de cálculo de variações para as tabelas
def calculate_variations(df_current, df_previous):
    df_current_agg = df_current.groupby('NO_PAIS').agg(
        VL_FOB_2024=('VL_FOB', 'sum'),
        KG_LIQUIDO_2024=('KG_LIQUIDO', 'sum')
    ).reset_index()

    df_previous_agg = df_previous.groupby('NO_PAIS').agg(
        VL_FOB_2023=('VL_FOB', 'sum'),
        KG_LIQUIDO_2023=('KG_LIQUIDO', 'sum')
    ).reset_index()

    # Juntar os dois anos
    df_merged = pd.merge(df_current_agg, df_previous_agg, on='NO_PAIS', how='outer').fillna(0)

    # Calcular o preço médio para ambos os anos
    df_merged['Preço Médio 2024'] = df_merged['VL_FOB_2024'] / df_merged['KG_LIQUIDO_2024']
    df_merged['Preço Médio 2023'] = df_merged['VL_FOB_2023'] / df_merged['KG_LIQUIDO_2023']

    # Calcular as variações
    df_merged['Variação (%) FOB'] = ((df_merged['VL_FOB_2024'] - df_merged['VL_FOB_2023']) / df_merged['VL_FOB_2023'] * 100).fillna(0)
    df_merged['Variação (%) Kg'] = ((df_merged['KG_LIQUIDO_2024'] - df_merged['KG_LIQUIDO_2023']) / df_merged['KG_LIQUIDO_2023'] * 100).fillna(0)
    df_merged['Variação (%) Preço Médio'] = ((df_merged['Preço Médio 2024'] - df_merged['Preço Médio 2023']) / df_merged['Preço Médio 2023'] * 100).fillna(0)
    
    # Substituir Infinitos por 100 para casos de 0 para 2023
    df_merged.replace([float('inf'), float('-inf')], 100, inplace=True)
    
    return df_merged

# Cálculo para Exportações
df_exp_variations = calculate_variations(df_exp, df_exp_2023)
total_fob_exp = df_exp_variations['VL_FOB_2024'].sum()
df_exp_variations['Participacao (%)'] = (df_exp_variations['VL_FOB_2024'] / total_fob_exp) * 100
df_exp_variations_sorted = df_exp_variations.sort_values(by='VL_FOB_2024', ascending=False).reset_index(drop=True)

# Cálculo para Importações
df_imp_variations = calculate_variations(df_imp, df_imp_2023)
total_fob_imp = df_imp_variations['VL_FOB_2024'].sum()
df_imp_variations['Participacao (%)'] = (df_imp_variations['VL_FOB_2024'] / total_fob_imp) * 100
df_imp_variations_sorted = df_imp_variations.sort_values(by='VL_FOB_2024', ascending=False).reset_index(drop=True)

with col8:
    st.subheader(f"Destinos de Exportação (Maiores Países)")
    if not df_exp.empty:
        st.dataframe(
            df_exp_variations_sorted.rename(columns={
                'NO_PAIS': 'País',
                'VL_FOB_2024': 'Valor FOB (US$)',
                'KG_LIQUIDO_2024': 'Total Kg',
                'Preço Médio 2024': 'Preço Médio (US$/Kg)'
            })[['País', 'Valor FOB (US$)', 'Total Kg', 'Participacao (%)', 'Preço Médio (US$/Kg)',
                'Variação (%) FOB', 'Variação (%) Kg', 'Variação (%) Preço Médio']].style.format({
                'Valor FOB (US$)': lambda x: format_brl(x, 2),
                'Total Kg': lambda x: format_brl(x, 0),
                'Participacao (%)': '{:.2f}%',
                'Preço Médio (US$/Kg)': '{:.2f}',
                'Variação (%) FOB': '{:.2f}%',
                'Variação (%) Kg': '{:.2f}%',
                'Variação (%) Preço Médio': '{:.2f}%',
            }),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("Não há dados de exportação para a seleção atual.")

with col9:
    st.subheader(f"Origens de Importação (Maiores Países)")
    if not df_imp.empty:
        st.dataframe(
            df_imp_variations_sorted.rename(columns={
                'NO_PAIS': 'País',
                'VL_FOB_2024': 'Valor FOB (US$)',
                'KG_LIQUIDO_2024': 'Total Kg',
                'Preço Médio 2024': 'Preço Médio (US$/Kg)'
            })[['País', 'Valor FOB (US$)', 'Total Kg', 'Participacao (%)', 'Preço Médio (US$/Kg)',
                'Variação (%) FOB', 'Variação (%) Kg', 'Variação (%) Preço Médio']].style.format({
                'Valor FOB (US$)': lambda x: format_brl(x, 2),
                'Total Kg': lambda x: format_brl(x, 0),
                'Participacao (%)': '{:.2f}%',
                'Preço Médio (US$/Kg)': '{:.2f}',
                'Variação (%) FOB': '{:.2f}%',
                'Variação (%) Kg': '{:.2f}%',
                'Variação (%) Preço Médio': '{:.2f}%',
            }),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("Não há dados de importação para a seleção atual.")

# --- 5. Treemaps de Países (Visão Geral) ---
st.markdown("---")
col10, col11 = st.columns(2)

with col10:
    st.subheader(f"Exportações (Total Geral) ({selected_year})")
    df_exp_geral = df_exp.groupby('NO_PAIS').agg(
        VL_FOB=('VL_FOB', 'sum'),
        KG_LIQUIDO=('KG_LIQUIDO', 'sum')
    ).reset_index()

    fig_exp_geral = px.treemap(
        df_exp_geral,
        path=['NO_PAIS'],
        values='VL_FOB',
        title=f'Destinos de Exportações por País (Todos os Produtos) ({selected_year})',
        color_discrete_sequence=px.colors.qualitative.D3,
        hover_name='NO_PAIS',
        hover_data={
            'VL_FOB': ':,2f',
            'KG_LIQUIDO': ':,0f'
        }
    )
    st.plotly_chart(fig_exp_geral, use_container_width=True)

with col11:
    st.subheader(f"Importações (Total Geral) ({selected_year})")
    df_imp_geral = df_imp.groupby('NO_PAIS').agg(
        VL_FOB=('VL_FOB', 'sum'),
        KG_LIQUIDO=('KG_LIQUIDO', 'sum')
    ).reset_index()

    fig_imp_geral = px.treemap(
        df_imp_geral,
        path=['NO_PAIS'],
        values='VL_FOB',
        title=f'Origens das Importações por País (Todos os Produtos) ({selected_year})',
        color_discrete_sequence=px.colors.qualitative.D3,
        hover_name='NO_PAIS',
        hover_data={
            'VL_FOB': ':,2f',
            'KG_LIQUIDO': ':,0f'
        }
    )
    st.plotly_chart(fig_imp_geral, use_container_width=True)
