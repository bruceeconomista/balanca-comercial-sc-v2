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
    try:
        # AQUI ESTÁ A MUDANÇA CRUCIAL: 'sep=;'.
        # O arquivo CSV está formatado com ponto e vírgula, não com vírgula.
        # Adicionamos skipinitialspace=True para ignorar espaços após o delimitador
        df = pd.read_csv('balanca_comercial_sc.csv', sep=';', on_bad_lines='skip', skipinitialspace=True)
        
        # Limpa os espaços dos nomes das colunas
        df.columns = df.columns.str.strip()
        
        # A seguir, uma limpeza de dados para garantir que as colunas numéricas estejam corretas
        try:
            # Usamos pd.to_numeric para converter as colunas e coercer erros para NaN
            df['CO_ANO'] = pd.to_numeric(df['CO_ANO'].astype(str).str.strip(), errors='coerce').astype('Int64')
            df['CO_MES'] = pd.to_numeric(df['CO_MES'].astype(str).str.strip(), errors='coerce').astype('Int64')
            df['KG_LIQUIDO'] = pd.to_numeric(df['KG_LIQUIDO'].astype(str).str.strip(), errors='coerce').astype(float)
            df['VL_FOB'] = pd.to_numeric(df['VL_FOB'].astype(str).str.strip(), errors='coerce').astype(float)
            
            # Remove linhas com valores NaN após a conversão para evitar erros nos gráficos
            df.dropna(subset=['CO_ANO', 'CO_MES', 'KG_LIQUIDO', 'VL_FOB'], inplace=True)
            
            return df
        except KeyError as e:
            st.error(f"Erro ao processar os dados: A coluna {e} não foi encontrada no arquivo CSV. Verifique o cabeçalho do arquivo.")
            st.stop()
        except Exception as e:
            st.error(f"Erro inesperado durante o processamento de dados: {e}. Verifique se os valores nas colunas numéricas estão corretos.")
            st.stop()

    except FileNotFoundError:
        st.error("Erro: O arquivo 'balanca_comercial_sc.csv' não foi encontrado. Por favor, verifique se ele foi adicionado corretamente ao seu repositório.")
        st.stop()

df_geral = carregar_dados()
    
# Verifica se o DataFrame foi carregado corretamente E se a coluna de ano não está vazia
if df_geral.empty or df_geral['CO_ANO'].isnull().all():
    st.error("Erro: O arquivo CSV foi lido, mas a coluna de anos está vazia ou contém apenas dados inválidos. Verifique o conteúdo do arquivo.")
else:
    # --- Sidebar ---
    with st.sidebar:
        st.title("Filtros")
        
        # Slider para selecionar o ano
        # Verifica se a coluna 'CO_ANO' possui valores válidos antes de obter min/max
        try:
            min_ano = int(df_geral['CO_ANO'].min())
            max_ano = int(df_geral['CO_ANO'].max())
        except (ValueError, TypeError):
            st.warning("Não foi possível determinar os anos do conjunto de dados. Usando valores padrão.")
            min_ano = 2020  # Valor padrão em caso de erro
            max_ano = 2023  # Valor padrão em caso de erro

        ano_selecionado = st.slider(
            "Ano",
            min_value=min_ano,
            max_value=max_ano,
            value=max_ano
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
