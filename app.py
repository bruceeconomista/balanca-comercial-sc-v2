import streamlit as st
import pandas as pd
import altair as alt
import plotly.express as px
from datasets import load_dataset

try:
    st.set_page_config(
        page_title="Análise de Balança Comercial",
        layout="wide"
    )

    st.title("Balança Comercial de Santa Catarina")
    st.subheader("Análise Detalhada de Exportações e Importações")
    st.markdown("---")

    @st.cache_data(show_spinner=False)
    def load_data():
        """
        Carrega os dados dos datasets públicos do Hugging Face.
        Usa o cache do Streamlit para evitar recarregar a cada interação.
        """
        try:
            with st.spinner('Carregando dados, isso pode levar alguns segundos...'):
                exp_dataset = load_dataset("bruceeconomista/balanca_comercial_exp_sc", split="train")
                imp_dataset = load_dataset("bruceeconomista/balanca_comercial_imp_sc", split="train")

                df_exp = exp_dataset.to_pandas()
                df_imp = imp_dataset.to_pandas()
            
            return df_exp, df_imp
        except Exception as e:
            st.error(f"Erro ao carregar os dados. Verifique a conexão ou os datasets: {e}")
            st.stop()
            return pd.DataFrame(), pd.DataFrame()

    df_exp, df_imp = load_data()

    if df_exp.empty or df_imp.empty:
        st.warning("Não foi possível carregar os dados. Por favor, tente novamente mais tarde.")
        st.stop()

    df_exp['tipo'] = 'Exportação'
    df_imp['tipo'] = 'Importação'

    df_exp.columns = df_exp.columns.str.replace('NO_PAIS_DESTINO', 'NO_PAIS')
    df_imp.columns = df_imp.columns.str.replace('NO_PAIS_ORIGEM', 'NO_PAIS')
    df_imp.columns = df_imp.columns.str.replace('CO_PAIS_ORIGEM', 'CO_PAIS')
    
    df = pd.concat([df_exp, df_imp], ignore_index=True)

    # --- Sidebar com Filtros ---
    st.sidebar.header("Filtros")

    # Filtro por Tipo (Exportação/Importação)
    tipo_selecionado = st.sidebar.selectbox("Tipo", ['Exportação', 'Importação', 'Ambos'], index=2)
    
    if tipo_selecionado == 'Exportação':
        df_filtered = df[df['tipo'] == 'Exportação']
    elif tipo_selecionado == 'Importação':
        df_filtered = df[df['tipo'] == 'Importação']
    else:
        df_filtered = df

    # Filtro por Ano
    anos_disponiveis = sorted(df_filtered['CO_ANO'].unique(), reverse=True)
    ano_selecionado = st.sidebar.selectbox("Ano", anos_disponiveis)
    df_filtered_ano = df_filtered[df_filtered['CO_ANO'] == ano_selecionado]

    # Filtro por Mês
    meses_disponiveis = sorted(df_filtered_ano['CO_MES'].unique())
    mes_selecionado = st.sidebar.selectbox("Mês", meses_disponiveis)
    df_filtered_mes = df_filtered_ano[df_filtered_ano['CO_MES'] == mes_selecionado]

    # Filtro por País
    paises_disponiveis = sorted(df_filtered_mes['NO_PAIS'].unique())
    pais_selecionado = st.sidebar.selectbox("País", ['Todos'] + paises_disponiveis)

    if pais_selecionado != 'Todos':
        df_filtered_pais = df_filtered_mes[df_filtered_mes['NO_PAIS'] == pais_selecionado]
    else:
        df_filtered_pais = df_filtered_mes

    # Filtro por Tipo de Produto
    produtos_disponiveis = sorted(df_filtered_pais['NO_SH4'].unique())
    produto_selecionado = st.sidebar.selectbox("Produto", ['Todos'] + produtos_disponiveis)
    
    if produto_selecionado != 'Todos':
        df_final = df_filtered_pais[df_filtered_pais['NO_SH4'] == produto_selecionado]
    else:
        df_final = df_filtered_pais

    # --- Exibição do Título Principal e Gráficos ---

    if not df_final.empty:
        total_vl_fob = df_final['VL_FOB'].sum()
        total_kg_liquido = df_final['KG_LIQUIDO'].sum()

        st.markdown(f"**Total FOB:** ${total_vl_fob:,.2f} | **Total KG:** {total_kg_liquido:,.2f} kg")

        st.markdown("---")
        
        # Gráficos de Treemap
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Balança Comercial por Tipo")
            df_tipo = df_final.groupby('tipo', dropna=False).agg(
                VL_FOB=('VL_FOB', 'sum')
            ).reset_index()
            fig_tipo = px.treemap(
                df_tipo,
                path=['tipo'],
                values='VL_FOB',
                title=f'Distribuição de {tipo_selecionado} por Tipo',
                color_discrete_sequence=px.colors.qualitative.D3,
                hover_name='tipo',
                hover_data={'VL_FOB': ':,2f'}
            )
            st.plotly_chart(fig_tipo, use_container_width=True)

        with col2:
            st.subheader("Balança Comercial por Via")
            df_via = df_final.groupby('NO_VIA', dropna=False).agg(
                VL_FOB=('VL_FOB', 'sum')
            ).reset_index()
            fig_via = px.treemap(
                df_via,
                path=['NO_VIA'],
                values='VL_FOB',
                title=f'Distribuição de {tipo_selecionado} por Via de Transporte',
                color_discrete_sequence=px.colors.qualitative.D3,
                hover_name='NO_VIA',
                hover_data={'VL_FOB': ':,2f'}
            )
            st.plotly_chart(fig_via, use_container_width=True)

        # Gráfico de Barras por País
        st.markdown("---")
        st.subheader("Top Países Parceiros")
        df_paises = df_final.groupby('NO_PAIS', dropna=False).agg(
            VL_FOB=('VL_FOB', 'sum')
        ).reset_index().nlargest(10, 'VL_FOB')

        fig_paises = px.bar(
            df_paises,
            x='NO_PAIS',
            y='VL_FOB',
            title=f'Valor FOB por País (Top 10)',
            color='VL_FOB',
            color_continuous_scale=px.colors.sequential.Viridis,
            hover_data={'VL_FOB': ':,2f'}
        )
        st.plotly_chart(fig_paises, use_container_width=True)
        
        # Gráfico de Barras por Produto
        st.markdown("---")
        st.subheader("Top Produtos")
        df_produtos = df_final.groupby('NO_PRODUTO', dropna=False).agg(
            VL_FOB=('VL_FOB', 'sum')
        ).reset_index().nlargest(10, 'VL_FOB')
        
        fig_produtos = px.bar(
            df_produtos,
            x='NO_PRODUTO',
            y='VL_FOB',
            title=f'Valor FOB por Produto (Top 10)',
            color='VL_FOB',
            color_continuous_scale=px.colors.sequential.Viridis,
            hover_data={'VL_FOB': ':,2f'}
        )
        st.plotly_chart(fig_produtos, use_container_width=True)
        
    else:
        st.info("Nenhum dado encontrado com os filtros selecionados.")

except Exception as e:
    st.error("Ocorreu um erro inesperado. Por favor, verifique se os arquivos de dados e as dependências estão corretos.")
    st.error(f"Detalhes do erro: {e}")
