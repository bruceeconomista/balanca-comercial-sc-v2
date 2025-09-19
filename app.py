import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Configura a página
st.set_page_config(
    page_title="Balança Comercial de Santa Catarina",
    page_icon="🇧🇷",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Use @st.cache_data para carregar os dados uma única vez e melhorar a performance
@st.cache_data
def carregar_dados():
    # AQUI ESTÁ A MUDANÇA CRUCIAL: 'sep=;'.
    # O arquivo CSV está formatado com ponto e vírgula, não com vírgula.
    df = pd.read_csv('balanca_comercial_sc.csv', sep=';')
    
    # A seguir, uma limpeza de dados para garantir que as colunas numéricas estejam corretas
    df['CO_ANO'] = df['CO_ANO'].astype(int)
    df['CO_MES'] = df['CO_MES'].astype(int)
    df['KG_LIQUIDO'] = df['KG_LIQUIDO'].astype(float)
    df['VL_FOB'] = df['VL_FOB'].astype(float)
    return df

try:
    df_geral = carregar_dados()
except FileNotFoundError:
    st.error("Erro: O arquivo 'balanca_comercial_sc.csv' não foi encontrado. Por favor, verifique se ele foi adicionado corretamente ao seu repositório.")
    st.stop()
    
# Verifica se o DataFrame foi carregado corretamente
if df_geral.empty:
    st.error("Erro: O arquivo CSV foi lido, mas está vazio. Verifique a formatação do arquivo.")
else:
    # --- Sidebar ---
    with st.sidebar:
        st.title("Filtros")
        
        # Slider para selecionar o ano
        ano_selecionado = st.slider(
            "Ano",
            min_value=int(df_geral['CO_ANO'].min()),
            max_value=int(df_geral['CO_ANO'].max()),
            value=int(df_geral['CO_ANO'].max())
        )
        
    # --- Conteúdo Principal ---
    st.title(f"Balança Comercial de SC - {ano_selecionado}")
    
    # Filtra os dados com base no ano selecionado
    df_filtrado = df_geral[df_geral['CO_ANO'] == ano_selecionado]
    
    # Cria colunas para exibir métricas
    col1, col2, col3 = st.columns(3)
    
    # CÁLCULO DAS MÉTRICAS
    exportacao_total = df_filtrado[df_filtrado['NO_EXP'].str.strip() != '-']['VL_FOB'].sum()
    importacao_total = df_filtrado[df_filtrado['NO_IMP'].str.strip() != '-']['VL_FOB'].sum()
    saldo_comercial = exportacao_total - importacao_total
    
    with col1:
        st.metric("Total Exportado (FOB)", f"US$ {exportacao_total:,.2f}")
    with col2:
        st.metric("Total Importado (FOB)", f"US$ {importacao_total:,.2f}")
    with col3:
        st.metric("Saldo Comercial", f"US$ {saldo_comercial:,.2f}")
        
    # Gráfico de barras de exportação por país
    st.header("Top 10 Países Exportadores e Importadores")
    
    col4, col5 = st.columns(2)
    
    with col4:
        st.subheader("Top 10 Exportações")
        df_exp = df_filtrado[df_filtrado['NO_EXP'].str.strip() != '-']
        if not df_exp.empty:
            df_top_exp = df_exp.groupby('NO_PAIS_DESTINO')['VL_FOB'].sum().nlargest(10).reset_index()
            fig_exp = px.bar(df_top_exp, x='NO_PAIS_DESTINO', y='VL_FOB', title="Exportações (FOB)",
                             labels={'NO_PAIS_DESTINO': 'País Destino', 'VL_FOB': 'Valor FOB (US$)'})
            st.plotly_chart(fig_exp, use_container_width=True)
        else:
            st.info("Não há dados de exportação para o ano selecionado.")
            
    with col5:
        st.subheader("Top 10 Importações")
        df_imp = df_filtrado[df_filtrado['NO_IMP'].str.strip() != '-']
        if not df_imp.empty:
            df_top_imp = df_imp.groupby('NO_PAIS_ORIGEM')['VL_FOB'].sum().nlargest(10).reset_index()
            fig_imp = px.bar(df_top_imp, x='NO_PAIS_ORIGEM', y='VL_FOB', title="Importações (FOB)",
                             labels={'NO_PAIS_ORIGEM': 'País Origem', 'VL_FOB': 'Valor FOB (US$)'})
            st.plotly_chart(fig_imp, use_container_width=True)
        else:
            st.info("Não há dados de importação para o ano selecionado.")

    # Gráfico de linhas do saldo comercial ao longo do tempo (todos os anos)
    st.header("Saldo Comercial Anual")
    df_agrupado = df_geral.groupby('CO_ANO').agg(
        exportacoes=('VL_FOB', lambda x: x[df_geral.loc[x.index, 'NO_EXP'].str.strip() != '-'].sum()),
        importacoes=('VL_FOB', lambda x: x[df_geral.loc[x.index, 'NO_IMP'].str.strip() != '-'].sum())
    ).reset_index()
    
    df_agrupado['saldo'] = df_agrupado['exportacoes'] - df_agrupado['importacoes']
    
    fig_saldo = px.line(df_agrupado, x='CO_ANO', y='saldo', title="Saldo Comercial (Exportação - Importação) ao longo dos anos")
    fig_saldo.update_traces(mode='lines+markers')
    st.plotly_chart(fig_saldo, use_container_width=True)

    # Exibindo os dados brutos
    st.header("Dados Brutos")
    st.dataframe(df_filtrado)
