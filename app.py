import streamlit as st
import pandas as pd
import requests
import io
import plotly.express as px
import altair as alt

try:
    # Configura a página do Streamlit
    st.set_page_config(
        page_title="Análise de Balança Comercial",
        layout="wide"
    )

    st.title("Balança Comercial de Santa Catarina")

    # URLs para os arquivos CSV no Hugging Face Hub.
    # Por favor, verifique se estes arquivos estão no seu repositório.
    EXP_URL = "https://huggingface.co/datasets/bruceeconomista/balanca-comercial-sc-v2-dados/resolve/main/EXP_TOTAL.csv?download=true"
    IMP_URL = "https://huggingface.co/datasets/bruceeconomista/balanca-comercial-sc-v2-dados/resolve/main/IMP_TOTAL.csv?download=true"

    def validate_columns(df, required_columns):
        """
        Verifica se as colunas necessárias estão presentes no DataFrame.
        Retorna True se todas as colunas existirem, caso contrário retorna False e a lista de colunas faltantes.
        """
        missing_columns = [col for col in required_columns if col not in df.columns]
        return not missing_columns, missing_columns

    @st.cache_data
    def load_data_from_huggingface():
        """
        Baixa e carrega os dados dos arquivos CSV a partir do Hugging Face Hub.
        Usa o cache do Streamlit para evitar recarregar a cada interação.
        """
        required_columns = ['CO_ANO', 'SG_UF', 'NO_PAIS', 'NO_NCM_POR', 'VL_FOB', 'KG_LIQUIDO']

        try:
            st.info("Baixando dados do Hugging Face Hub. Isso pode levar alguns minutos...")

            # Baixar o arquivo de exportação
            response_exp = requests.get(EXP_URL)
            if response_exp.status_code != 200:
                st.error(f"Erro ao baixar o arquivo de exportação. Status: {response_exp.status_code}")
                st.stop()

            # Baixar o arquivo de importação
            response_imp = requests.get(IMP_URL)
            if response_imp.status_code != 200:
                st.error(f"Erro ao baixar o arquivo de importação. Status: {response_imp.status_code}")
                st.stop()

            df_exp = pd.read_csv(io.StringIO(response_exp.text))
            df_imp = pd.read_csv(io.StringIO(response_imp.text))

            # Limpar os nomes das colunas de forma defensiva
            df_exp.columns = [col.replace('ï»¿', '').strip() for col in df_exp.columns]
            df_imp.columns = [col.replace('ï»¿', '').strip() for col in df_imp.columns]

            # Validar as colunas
            exp_valid, exp_missing = validate_columns(df_exp, required_columns)
            imp_valid, imp_missing = validate_columns(df_imp, required_columns)

            if not exp_valid:
                st.error(f"Erro: As seguintes colunas estão faltando no arquivo de exportação: {exp_missing}")
                st.stop()
            if not imp_valid:
                st.error(f"Erro: As seguintes colunas estão faltando no arquivo de importação: {imp_missing}")
                st.stop()
            
            return df_exp, df_imp
        except Exception as e:
            st.error("Ocorreu um erro ao carregar os dados. Verifique a URL e a integridade dos arquivos.")
            st.exception(e) # Mostra o erro completo
            st.stop()
            return pd.DataFrame(), pd.DataFrame()

    # Inicia o carregamento dos dados
    with st.spinner("Carregando dados..."):
        df_exp_total, df_imp_total = load_data_from_huggingface()

    # Verifica se os DataFrames foram carregados com sucesso
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

        # Filtra os dados de SC e ano selecionado
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

        # --- Gráficos de Análise
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
        st.warning("Aguardando dados... Certifique-se de que as URLs no código estão corretas e o seu repositório está acessível.")

except Exception as e:
    st.error("Ocorreu um erro inesperado na sua aplicação.")
    st.exception(e)
