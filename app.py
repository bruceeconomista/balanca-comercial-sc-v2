import streamlit as st
import pandas as pd
import altair as alt
import plotly.express as px
import os

try:
    st.set_page_config(
        page_title="Análise de Balança Comercial",
        layout="wide"
    )

    st.title("Balança Comercial de Santa Catarina")

    # Define o caminho dos arquivos
    exp_file_path = "parquet_files/EXP_TOTAL.parquet"
    imp_file_path = "parquet_files/IMP_TOTAL.parquet"
    
    st.write(f"Verificando a existência dos arquivos...")
    
    # Verifica se os arquivos existem no caminho esperado
    if not os.path.exists(exp_file_path):
        st.error(f"Erro: O arquivo '{exp_file_path}' não foi encontrado.")
        st.stop()
    if not os.path.exists(imp_file_path):
        st.error(f"Erro: O arquivo '{imp_file_path}' não foi encontrado.")
        st.stop()

    @st.cache_data
    def load_data():
        """
        Carrega os dados dos arquivos Parquet usando o cache do Streamlit.
        """
        try:
            st.write("Lendo os arquivos Parquet...")
            df_exp = pd.read_parquet(exp_file_path)
            df_imp = pd.read_parquet(imp_file_path)
            
            # Limpar os nomes das colunas
            df_exp.columns = [col.replace('ï»¿', '') for col in df_exp.columns]
            df_imp.columns = [col.replace('ï»¿', '') for col in df_imp.columns]
            
            return df_exp, df_imp
        except Exception as e:
            st.error(f"Erro ao ler os arquivos Parquet. Detalhes: {e}")
            return pd.DataFrame(), pd.DataFrame()

    with st.spinner("Carregando dados..."):
        df_exp_total, df_imp_total = load_data()

    if not df_exp_total.empty and not df_imp_total.empty:
        st.success("Dados carregados com sucesso!")
        
        # --- Filtros
        st.sidebar.header("Filtros")
        years_exp = sorted(df_exp_total['CO_ANO'].unique()) if 'CO_ANO' in df_exp_total.columns else []
        selected_year_exp = st.sidebar.selectbox("Selecione o Ano de Exportação", years_exp)

        years_imp = sorted(df_imp_total['CO_ANO'].unique()) if 'CO_ANO' in df_imp_total.columns else []
        selected_year_imp = st.sidebar.selectbox("Selecione o Ano de Importação", years_imp)

        # --- Processamento e Visualização
        st.subheader(f"Análise de Balança Comercial em {selected_year_exp} e {selected_year_imp}")

        df_exp_filtered_sc = df_exp_total[(df_exp_total['SG_UF'] == 'SC') & (df_exp_total['CO_ANO'] == selected_year_exp)]
        df_imp_filtered_sc = df_imp_total[(df_imp_total['SG_UF'] == 'SC') & (df_imp_total['CO_ANO'] == selected_year_imp)]

        # --- Indicadores Gerais
        total_exp_sc = df_exp_filtered_sc['VL_FOB'].sum()
        total_imp_sc = df_imp_filtered_sc['VL_FOB'].sum()
        balanca_comercial = total_exp_sc - total_imp_sc

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Exportações (SC)", f"US$ {total_exp_sc:,.2f}")
        with col2:
            st.metric("Total Importações (SC)", f"US$ {total_imp_sc:,.2f}")
        with col3:
            st.metric("Balança Comercial (SC)", f"US$ {balanca_comercial:,.2f}")
        
        # --- Gráficos
        col11, col12, col13 = st.columns(3)

        with col11:
            st.subheader("Exportações por Produto")
            if not df_exp_filtered_sc.empty:
                df_exp_product = df_exp_filtered_sc.groupby('NO_NCM_POR', dropna=False).agg(
                    VL_FOB=('VL_FOB', 'sum'),
                    KG_LIQUIDO=('KG_LIQUIDO', 'sum')
                ).reset_index().sort_values(by='VL_FOB', ascending=False)
                df_exp_product = df_exp_product.head(10)

                fig_exp_prod = px.bar(
                    df_exp_product,
                    x='NO_NCM_POR',
                    y='VL_FOB',
                    title='Top 10 Produtos de Exportação',
                    labels={'NO_NCM_POR': 'Produto', 'VL_FOB': 'Valor FOB (US$)'},
                    color_discrete_sequence=px.colors.qualitative.D3,
                )
                st.plotly_chart(fig_exp_prod, use_container_width=True)
            else:
                st.info("Não há dados de exportação para a seleção atual.")

        with col12:
            st.subheader("Exportações (Total Geral)")
            if not df_exp_filtered_sc.empty:
                df_exp_geral = df_exp_filtered_sc.groupby('NO_PAIS', dropna=False).agg(
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
            else:
                st.info("Não há dados de exportação para a seleção atual.")

        with col13:
            st.subheader("Importações (Total Geral)")
            if not df_imp_filtered_sc.empty:
                df_imp_geral = df_imp_filtered_sc.groupby('NO_PAIS', dropna=False).agg(
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
            else:
                st.info("Não há dados de importação para a seleção atual.")
    else:
        st.warning("Não foi possível carregar os dados. Verifique o seu repositório no GitHub para garantir que os arquivos estão presentes e que o Git LFS foi configurado corretamente.")
        
except Exception as e:
    st.error("Ocorreu um erro inesperado. Por favor, tente novamente mais tarde.")
    st.error(f"Detalhes do erro: {e}")
