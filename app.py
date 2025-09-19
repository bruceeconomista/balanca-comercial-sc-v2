import streamlit as st
import pandas as pd
import os
import altair as alt
import plotly.express as px
import sys
import traceback

# O Streamlit é um framework para criar aplicativos da web com Python.
# O `try` inicia um bloco onde tentamos executar o código. Se um erro ocorrer,
# a execução salta para o bloco `except`.
try:
    st.set_page_config(
        page_title="Análise de Balança Comercial",
        layout="wide"
    )

    st.title("Balança Comercial de Santa Catarina")

    # Nomes dos arquivos
    EXP_FILE = "EXP_TOTAL.parquet"
    IMP_FILE = "IMP_TOTAL.parquet"
    PARQUET_FOLDER = "parquet_files"

    def load_data():
        """Carrega os dados dos arquivos Parquet."""
        try:
            exp_path = os.path.join(PARQUET_FOLDER, EXP_FILE)
            imp_path = os.path.join(PARQUET_FOLDER, IMP_FILE)

            df_exp = pd.read_parquet(exp_path)
            df_imp = pd.read_parquet(imp_path)
            
            # Limpar os nomes das colunas
            df_exp.columns = [col.replace('ï»¿', '') for col in df_exp.columns]
            df_imp.columns = [col.replace('ï»¿', '') for col in df_imp.columns]
            
            return df_exp, df_imp
        except FileNotFoundError:
            st.error("Erro: Os arquivos .parquet não foram encontrados. Certifique-se de que estão na pasta 'parquet_files'.")
            st.stop()
            return pd.DataFrame(), pd.DataFrame()

    df_exp, df_imp = load_data()

    # Combinar os dataframes para obter os anos disponíveis
    if not df_exp.empty and not df_imp.empty:
        df_geral = pd.concat([df_exp, df_imp])
        anos_validos = df_geral['CO_ANO'].unique().tolist()
    elif not df_exp.empty:
        anos_validos = df_exp['CO_ANO'].unique().tolist()
    elif not df_imp.empty:
        anos_validos = df_imp['CO_ANO'].unique().tolist()
    else:
        anos_validos = []

    # --- 1. Filtros na Primeira Linha ---
    col1, col2 = st.columns(2)

    with col1:
        # A verificação 'if not df_exp.empty' é crucial para evitar erros se os dados não forem carregados
        if not df_exp.empty:
            all_ufs = df_exp['SG_UF_NCM'].unique().tolist()
            default_ufs = ['SC'] if 'SC' in all_ufs else all_ufs
            selected_ufs = st.multiselect(
                "Selecione os Estados (UF)",
                options=all_ufs,
                default=default_ufs
            )
        else:
            selected_ufs = []
    
    with col2:
        if anos_validos:
            min_ano = int(min(anos_validos))
            max_ano = int(max(anos_validos))
            ano_selecionado = st.slider(
                "Ano",
                min_value=min_ano,
                max_value=max_ano,
                value=max_ano
            )
        else:
            st.warning("Não foi possível determinar os anos do conjunto de dados.")
            ano_selecionado = 2023 # Valor padrão em caso de erro

    # Cria os dataframes filtrados para os cards, gráficos e tabelas principais
    df_exp_filtered_sc = df_exp[
        (df_exp['CO_ANO'] == ano_selecionado) &
        (df_exp['SG_UF_NCM'].isin(selected_ufs))
    ]

    df_imp_filtered_sc = df_imp[
        (df_imp['CO_ANO'] == ano_selecionado) &
        (df_imp['SG_UF_NCM'].isin(selected_ufs))
    ]


    # --- 2. Cards de resumo ---
    st.markdown("---")
    col3, col4, col5 = st.columns(3)

    # Cálculo dos totais
    total_exp = df_exp_filtered_sc['VL_FOB'].sum()
    total_imp = df_imp_filtered_sc['VL_FOB'].sum()
    balanca_comercial = total_exp - total_imp

    def format_currency(value):
        return f"${value:,.2f}"

    with col3:
        st.metric(
            label="Total de Exportações",
            value=format_currency(total_exp)
        )

    with col4:
        st.metric(
            label="Total de Importações",
            value=format_currency(total_imp)
        )
        
    with col5:
        st.metric(
            label="Resultado da Balança Comercial",
            value=format_currency(balanca_comercial)
        )

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

    with col6:
        st.subheader("TAREFA 1 - Produtos Mais Exportados - Valor padrão = 5")
        num_products_exp = st.slider(
            "Número de produtos a exibir", min_value=0, max_value=20, value=5, key='slider_exp'
        )
        
        df_chart_exp = df_exp_filtered_sc.groupby(['CO_NCM', 'NO_NCM_POR']).agg(
            VL_FOB=('VL_FOB', 'sum'),
            KG_LIQUIDO=('KG_LIQUIDO', 'sum')
        ).nlargest(num_products_exp, 'VL_FOB').reset_index()

        df_chart_exp['VL_FOB_FORMATADO'] = df_chart_exp['VL_FOB'].apply(format_value)

        chart_exp = alt.Chart(df_chart_exp).mark_bar().encode(
            x=alt.X('CO_NCM:N', title='Código NCM', sort='-y'),
            y=alt.Y('VL_FOB', title='Valor FOB (US$)', axis=alt.Axis(format='~s')),
            tooltip=[
                alt.Tooltip('NO_NCM_POR', title='Nome do Produto'),
                alt.Tooltip('KG_LIQUIDO', title='Total de Kg', format=',.0f'),
                alt.Tooltip('VL_FOB', title='Valor FOB (US$)', format=',.2f')
            ]
        ).properties(
            title=f'{num_products_exp} Produtos Mais Exportados'
        )
        st.altair_chart(chart_exp, use_container_width=True)
        
        top_exp_products = df_chart_exp['NO_NCM_POR'].unique().tolist()


    with col7:
        st.subheader("Produtos Mais Importados - Valor padrão = 5")
        num_products_imp = st.slider(
            "Número de produtos a exibir", min_value=0, max_value=20, value=5, key='slider_imp'
        )

        df_chart_imp = df_imp_filtered_sc.groupby(['CO_NCM', 'NO_NCM_POR']).agg(
            VL_FOB=('VL_FOB', 'sum'),
            KG_LIQUIDO=('KG_LIQUIDO', 'sum')
        ).nlargest(num_products_imp, 'VL_FOB').reset_index()
        
        df_chart_imp['VL_FOB_FORMATADO'] = df_chart_imp['VL_FOB'].apply(format_value)
        
        chart_imp = alt.Chart(df_chart_imp).mark_bar(color='#E57F84').encode(
            x=alt.X('CO_NCM:N', title='Código NCM', sort='-y'),
            y=alt.Y('VL_FOB', title='Valor FOB (US$)', axis=alt.Axis(format='~s')),
            tooltip=[
                alt.Tooltip('NO_NCM_POR', title='Nome do Produto'),
                alt.Tooltip('KG_LIQUIDO', title='Total de Kg', format=',.0f'),
                alt.Tooltip('VL_FOB', title='Valor FOB (US$)', format=',.2f')
            ]
        ).properties(
            title=f'{num_products_imp} Produtos Mais Importados'
        )
        st.altair_chart(chart_imp, use_container_width=True)
        
        top_imp_products = df_chart_imp['NO_NCM_POR'].unique().tolist()


    # --- 4. Treemaps de Países por Produto Selecionado ---
    st.markdown("---")
    st.header("TAREFA 1 - Fluxo de Exportação para os principais produtos")
    col8, col9 = st.columns(2)

    # Filtrar o DataFrame por produtos selecionados antes de agrupar para o treemap
    df_exp_filtered_products = df_exp_filtered_sc[df_exp_filtered_sc['NO_NCM_POR'].isin(top_exp_products)]
    df_imp_filtered_products = df_imp_filtered_sc[df_imp_filtered_sc['NO_NCM_POR'].isin(top_imp_products)]

    with col8:
        st.subheader("Exportações de Produtos por País")
        
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

    with col9:
        st.subheader("Importações de Produtos por País")

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
    ## Tarefa 2: Análise de Parceiros Comerciais e Competitividade Geral
    # ---
    # --- 5. Tabelas dos Maiores Países e Análise de Preço ---
    st.markdown("---")
    st.header("TAREFA 2 - Participação de cada país no total exportado / Tabela de resultados")

    col10, col11 = st.columns(2)

    # Código para a tabela de exportação
    with col10:
        st.subheader("10 Maiores Destinos de Exportação / Variações Interanuais")
        if not df_exp_filtered_sc.empty:
            df_exp_agg = df_exp[(df_exp['CO_ANO'].isin([2023, 2024])) & (df_exp['SG_UF_NCM'].isin(selected_ufs))]
            df_exp_agg = df_exp_agg.groupby(['CO_ANO', 'NO_PAIS']).agg(
                VL_FOB=('VL_FOB', 'sum'),
                KG_LIQUIDO=('KG_LIQUIDO', 'sum')
            ).reset_index()
            
            df_pivot = df_exp_agg.pivot_table(index='NO_PAIS', columns='CO_ANO', values=['VL_FOB', 'KG_LIQUIDO']).fillna(0)
            df_pivot.columns = [f'{metric}_{year}' for metric, year in df_pivot.columns]
            df_pivot = df_pivot.reset_index()

            df_pivot['Preço Médio 2023 (US$/Kg)'] = df_pivot.apply(
                lambda row: row['VL_FOB_2023'] / row['KG_LIQUIDO_2023'] if row['KG_LIQUIDO_2023'] > 0 else 0, axis=1
            )
            df_pivot['Preço Médio 2024 (US$/Kg)'] = df_pivot.apply(
                lambda row: row['VL_FOB_2024'] / row['KG_LIQUIDO_2024'] if row['KG_LIQUIDO_2024'] > 0 else 0, axis=1
            )

            df_pivot['Var. Preço 24/23 (%)'] = df_pivot.apply(
                lambda row: ((row['Preço Médio 2024 (US$/Kg)'] - row['Preço Médio 2023 (US$/Kg)']) / row['Preço Médio 2023 (US$/Kg)'] * 100) if row['Preço Médio 2023 (US$/Kg)'] > 0 else 0, axis=1
            )
            
            total_fob_2024 = df_pivot['VL_FOB_2024'].sum()
            df_pivot['Participacao (%)'] = (df_pivot['VL_FOB_2024'] / total_fob_2024) * 100 if total_fob_2024 > 0 else 0
            
            top_10_exp = df_pivot.nlargest(10, 'VL_FOB_2024').reset_index(drop=True)
            top_10_exp = top_10_exp.rename(columns={
                'NO_PAIS': 'País',
                'VL_FOB_2024': 'Valor FOB (US$)',
                'KG_LIQUIDO_2024': 'Total Kg'
            })
            
            top_10_exp_display = top_10_exp[['País', 'Valor FOB (US$)', 'Total Kg', 'Participacao (%)', 'Preço Médio 2023 (US$/Kg)', 'Preço Médio 2024 (US$/Kg)', 'Var. Preço 24/23 (%)']]

            st.dataframe(
                top_10_exp_display.style.format({
                    'Valor FOB (US$)': '{:,.2f}',
                    'Total Kg': '{:,.0f}',
                    'Participacao (%)': '{:.2f}%',
                    'Preço Médio 2023 (US$/Kg)': '{:.2f}',
                    'Preço Médio 2024 (US$/Kg)': '{:.2f}',
                    'Var. Preço 24/23 (%)': '{:.2f}%',
                }),
                use_container_width=True
            )
        else:
            st.info("Não há dados de exportação para a seleção atual.")


    # Código para a tabela de importação
    with col11:
        st.subheader("10 Maiores Destinos de Importação / Variações Interanuais")
        if not df_imp_filtered_sc.empty:
            df_imp_agg = df_imp[(df_imp['CO_ANO'].isin([2023, 2024])) & (df_imp['SG_UF_NCM'].isin(selected_ufs))]
            df_imp_agg = df_imp_agg.groupby(['CO_ANO', 'NO_PAIS']).agg(
                VL_FOB=('VL_FOB', 'sum'),
                KG_LIQUIDO=('KG_LIQUIDO', 'sum')
            ).reset_index()

            df_imp_pivot = df_imp_agg.pivot_table(index='NO_PAIS', columns='CO_ANO', values=['VL_FOB', 'KG_LIQUIDO']).fillna(0)
            df_imp_pivot.columns = [f'{metric}_{year}' for metric, year in df_imp_pivot.columns]
            df_imp_pivot = df_imp_pivot.reset_index()

            df_imp_pivot['Preço Médio 2023 (US$/Kg)'] = df_imp_pivot.apply(
                lambda row: row['VL_FOB_2023'] / row['KG_LIQUIDO_2023'] if row['KG_LIQUIDO_2023'] > 0 else 0, axis=1
            )
            df_imp_pivot['Preço Médio 2024 (US$/Kg)'] = df_imp_pivot.apply(
                lambda row: row['VL_FOB_2024'] / row['KG_LIQUIDO_2024'] if row['KG_LIQUIDO_2024'] > 0 else 0, axis=1
            )
            df_imp_pivot['Var. Preço 24/23 (%)'] = df_imp_pivot.apply(
                lambda row: ((row['Preço Médio 2024 (US$/Kg)'] - row['Preço Médio 2023 (US$/Kg)']) / row['Preço Médio 2023 (US$/Kg)'] * 100) if row['Preço Médio 2023 (US$/Kg)'] > 0 else 0, axis=1
            )
            
            total_imp_2024 = df_imp_pivot['VL_FOB_2024'].sum()
            df_imp_pivot['Participacao (%)'] = (df_imp_pivot['VL_FOB_2024'] / total_imp_2024) * 100 if total_imp_2024 > 0 else 0

            top_10_imp = df_imp_pivot.nlargest(10, 'VL_FOB_2024').reset_index(drop=True)
            top_10_imp = top_10_imp.rename(columns={
                'NO_PAIS': 'País',
                'VL_FOB_2024': 'Valor FOB (US$)',
                'KG_LIQUIDO_2024': 'Total Kg'
            })
            
            top_10_imp_display = top_10_imp[['País', 'Valor FOB (US$)', 'Total Kg', 'Participacao (%)', 'Preço Médio 2023 (US$/Kg)', 'Preço Médio 2024 (US$/Kg)', 'Var. Preço 24/23 (%)']]
            
            st.dataframe(
                top_10_imp_display.style.format({
                    'Valor FOB (US$)': '{:,.2f}',
                    'Total Kg': '{:,.0f}',
                    'Participacao (%)': '{:.2f}%',
                    'Preço Médio 2023 (US$/Kg)': '{:.2f}',
                    'Preço Médio 2024 (US$/Kg)': '{:.2f}',
                    'Var. Preço 24/23 (%)': '{:.2f}%',
                }),
                use_container_width=True
            )
        else:
            st.info("Não há dados de importação para a seleção atual.")


    # --- 6. Treemaps de Países (Visão Geral) ---
    st.markdown("---")
    st.header("TAREFA 2 - Análise de Países por Total Geral de Comércio")
    col12, col13 = st.columns(2)

    with col12:
        st.subheader("Exportações (Total Geral)")
        df_exp_geral = df_exp_filtered_sc.groupby('NO_PAIS').agg(
            VL_FOB=('VL_FOB', 'sum'),
            KG_LIQUIDO=('KG_LIQUIDO', 'sum')
        ).reset_index()

        fig_exp_geral = px.treemap(
            df_exp_geral,
            path=['NO_PAIS'],
            values='VL_FOB',
            title='Distribuição de Exportações por País (Todos os Produtos)',
            color_discrete_sequence=px.colors.qualitative.D3,
            hover_name='NO_PAIS',
            hover_data={
                'VL_FOB': ':,2f',
                'KG_LIQUIDO': ':,0f'
            }
        )
        st.plotly_chart(fig_exp_geral, use_container_width=True)

    with col13:
        st.subheader("Importações (Total Geral)")
        df_imp_geral = df_imp_filtered_sc.groupby('NO_PAIS').agg(
            VL_FOB=('VL_FOB', 'sum'),
            KG_LIQUIDO=('KG_LIQUIDO', 'sum')
        ).reset_index()

        fig_imp_geral = px.treemap(
            df_imp_geral,
            path=['NO_PAIS'],
            values='VL_FOB',
            title='Distribuição de Importações por País (Todos os Produtos)',
            color_discrete_sequence=px.colors.qualitative.D3,
            hover_name='NO_PAIS',
            hover_data={
                'VL_FOB': ':,2f',
                'KG_LIQUIDO': ':,0f'
            }
        )
        st.plotly_chart(fig_imp_geral, use_container_width=True)

# O `except` é executado se qualquer erro (de qualquer tipo) ocorrer no bloco `try`.
except Exception as e:
    st.error("Ocorreu um erro inesperado ao executar o aplicativo. Por favor, entre em contato com o administrador.")
    st.write("---")
    st.header("Detalhes Técnicos do Erro")
    st.exception(e)
    st.write("---")
    st.text("Detalhes do Traceback:")
    st.code(traceback.format_exc())
    st.stop()
