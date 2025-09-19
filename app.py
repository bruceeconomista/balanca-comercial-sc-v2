import streamlit as st
import pandas as pd
import os
import altair as alt
import plotly.express as px

st.set_page_config(
    page_title="Análise de Balança Comercial",
    layout="wide"
)

st.title("Balança Comercial de Santa Catarina")

# Nomes dos arquivos e pasta de dados pré-processados
DATA_FOLDER = "pre_processed_data"

def load_data(selected_year):
    """
    Carrega os dados dos arquivos Parquet para o ano selecionado.
    Esta versão carrega arquivos que já estão pré-filtrados por UF e Ano.
    """
    try:
        exp_path = os.path.join(DATA_FOLDER, f"exp_products_{selected_year}.parquet")
        imp_path = os.path.join(DATA_FOLDER, f"imp_products_{selected_year}.parquet")

        df_exp = pd.read_parquet(exp_path)
        df_imp = pd.read_parquet(imp_path)
        
        return df_exp, df_imp
    except FileNotFoundError:
        st.error("Erro: Os arquivos .parquet não foram encontrados. Certifique-se de que estão na pasta 'pre_processed_data'.")
        return pd.DataFrame(), pd.DataFrame()

# --- 1. Filtros na Primeira Linha ---
col1, col2 = st.columns(2)

with col1:
    st.info("A análise de dados pré-processados está limitada à UF de SC.")
    selected_ufs = ['SC'] # Valor fixo para a análise pré-processada

with col2:
    all_years = [2024] # Define o ano de 2024 como a única opção
    selected_year = st.selectbox(
        "Selecione o Ano",
        options=all_years
    )

df_exp, df_imp = load_data(selected_year)

# --- 2. Cards de resumo ---
st.markdown("---")
col3, col4, col5 = st.columns(3)

if not df_exp.empty and not df_imp.empty:
    total_exp = df_exp['VL_FOB'].sum()
    total_imp = df_imp['VL_FOB'].sum()
    balanca_comercial = total_exp - total_imp

    def format_brl(value, decimals=2):
        return f"{value:,.{decimals}f}".replace(",", "X").replace(".", ",").replace("X", ".")

    def format_currency_br(value):
        return f"US$ {format_brl(value, 0)}"

    with col3:
        st.metric(
            label=f"Total de Exportações ({selected_year})",
            value=format_currency_br(total_exp)
        )

    with col4:
        st.metric(
            label=f"Total de Importações ({selected_year})",
            value=format_currency_br(total_imp)
        )
        
    with col5:
        st.metric(
            label=f"Resultado da Balança Comercial ({selected_year})",
            value=format_currency_br(balanca_comercial)
        )
else:
    st.info("Não há dados para exibir. Por favor, verifique se os arquivos estão na pasta correta.")

# ---
## Tarefa 1: Análise de Produtos e Países por Fluxo
# ---
# --- 3. Análise Gráfica (Produtos) ---
st.markdown("---")
col6, col7 = st.columns(2)

def format_value(value):
    if value >= 1_000_000_000:
        return f"{value / 1_000_000_000:.1f}B"
    if value >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    return str(value)

if not df_exp.empty:
    with col6:
        st.subheader("TAREFA 1 - Produtos Mais Exportados")
        num_products_exp = st.slider(
            "Número de produtos a exibir", min_value=0, max_value=20, value=5, key='slider_exp'
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
        st.subheader(f"Dados dos {num_products_exp} Produtos Mais Exportados")
        st.dataframe(df_chart_exp, use_container_width=True, hide_index=True)


if not df_imp.empty:
    with col7:
        st.subheader("Produtos Mais Importados")
        num_products_imp = st.slider(
            "Número de produtos a exibir", min_value=0, max_value=20, value=5, key='slider_imp'
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
        st.subheader(f"Dados dos {num_products_imp} Produtos Mais Importados")
        st.dataframe(df_chart_imp, use_container_width=True, hide_index=True)

# --- 4. Treemaps de Países por Produto Selecionado ---
st.markdown("---")
st.header("TAREFA 1 - Fluxo de Exportação e Importação por País (Principais Produtos)")
col8, col9 = st.columns(2)

if not df_exp.empty:
    with col8:
        st.subheader("Exportações dos Principais Produtos por País")
        if 'NO_PAIS' in df_exp.columns and 'NO_NCM_POR' in df_exp.columns:
            df_exp_filtered_products = df_exp[df_exp['NO_NCM_POR'].isin(top_exp_products)]
            
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
                    title='Distribuição de Exportações por País',
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
        else:
            st.info("Dados de exportação incompletos. 'NO_PAIS' ou 'NO_NCM_POR' não encontrados.")
else:
    with col8:
        st.info("Não há dados de exportação para exibir.")


if not df_imp.empty:
    with col9:
        st.subheader("Importações dos Principais Produtos por País")
        if 'NO_PAIS' in df_imp.columns and 'NO_NCM_POR' in df_imp.columns:
            df_imp_filtered_products = df_imp[df_imp['NO_NCM_POR'].isin(top_imp_products)]

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
        else:
            st.info("Dados de importação incompletos. 'NO_PAIS' ou 'NO_NCM_POR' não encontrados.")
else:
    with col9:
        st.info("Não há dados de importação para exibir.")

# ---
## Tarefa 2: Análise de Parceiros Comerciais e Competitividade Geral
# ---
# --- 5. Tabelas dos Maiores Países e Análise de Preço ---
st.markdown("---")
st.header("TAREFA 2 - Participação de cada país no total exportado / Tabela de resultados")

col10, col11 = st.columns(2)

if not df_exp.empty:
    with col10:
        st.subheader(f"Destinos de Exportação / Variações Interanuais ({selected_year} vs {selected_year-1})")
        if 'NO_PAIS' in df_exp.columns:
            # Esta parte do código requer dados do ano anterior, então precisa de um ajuste
            st.info("A análise de variação interanual requer dados de 2023. Seus arquivos pré-processados não contêm esses dados.")
        else:
            st.info("Dados de exportação incompletos. 'NO_PAIS' não encontrado.")
else:
    with col10:
        st.info("Não há dados de exportação para a seleção atual.")

if not df_imp.empty:
    with col11:
        st.subheader(f"Origens de Importação / Variações Interanuais ({selected_year} vs {selected_year-1})")
        if 'NO_PAIS' in df_imp.columns:
            # Esta parte do código requer dados do ano anterior, então precisa de um ajuste
            st.info("A análise de variação interanual requer dados de 2023. Seus arquivos pré-processados não contêm esses dados.")
        else:
            st.info("Dados de importação incompletos. 'NO_PAIS' não encontrado.")
else:
    with col11:
        st.info("Não há dados de importação para a seleção atual.")

# --- 6. Treemaps de Países (Visão Geral) ---
st.markdown("---")
st.header("TAREFA 2 - Análise de Países por Total Geral de Comércio")
col12, col13 = st.columns(2)

if not df_exp.empty:
    with col12:
        st.subheader(f"Exportações (Total Geral) ({selected_year})")
        if 'NO_PAIS' in df_exp.columns:
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
        else:
            st.info("Dados de exportação incompletos. 'NO_PAIS' não encontrado.")
else:
    with col12:
        st.info("Não há dados de exportação para exibir.")

if not df_imp.empty:
    with col13:
        st.subheader(f"Importações (Total Geral) ({selected_year})")
        if 'NO_PAIS' in df_imp.columns:
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
        else:
            st.info("Dados de importação incompletos. 'NO_PAIS' não encontrado.")
else:
    with col13:
        st.info("Não há dados de importação para exibir.")
