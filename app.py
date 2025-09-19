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
        df = pd.read_csv('balanca_comercial_sc.csv', sep=';', on_bad_lines='skip')

        # Conversões seguras
        df['CO_ANO'] = pd.to_numeric(df['CO_ANO'], errors='coerce').astype('Int64')
        df['CO_MES'] = pd.to_numeric(df['CO_MES'], errors='coerce').astype('Int64')
        df['KG_LIQUIDO'] = pd.to_numeric(df['KG_LIQUIDO'], errors='coerce').astype(float)
        df['VL_FOB'] = pd.to_numeric(df['VL_FOB'], errors='coerce').astype(float)

        # Remove linhas com valores críticos ausentes
        df.dropna(subset=['CO_ANO', 'CO_MES', 'KG_LIQUIDO', 'VL_FOB'], inplace=True)

        return df

    except KeyError as e:
        st.error(f"Erro ao processar os dados: coluna {e} não encontrada no CSV.")
        st.stop()
    except Exception as e:
        st.error(f"Erro inesperado durante o processamento: {e}")
        st.stop()

try:
    df_geral = carregar_dados()
except FileNotFoundError:
    st.error("Erro: O arquivo 'balanca_comercial_sc.csv' não foi encontrado. Adicione-o ao repositório.")
    st.stop()

# Verifica se o DataFrame foi carregado corretamente
if df_geral.empty or df_geral['CO_ANO'].isnull().all():
    st.error("Erro: O arquivo foi lido, mas a coluna CO_ANO está vazia ou inválida.")
    st.stop()

# --- Sidebar ---
with st.sidebar:
    st.title("Filtros")

    # Garantir que existam anos válidos
    anos_validos = df_geral['CO_ANO'].dropna().unique()
    if len(anos_validos) == 0:
        st.error("Não há anos válidos na base de dados.")
        st.stop()

    min_ano = int(min(anos_validos))
    max_ano = int(max(anos_validos))

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

# Cálculo das métricas (com checagens seguras)
if 'NO_EXP' in df_filtrado.columns and 'NO_IMP' in df_filtrado.columns:
    exportacao_total = df_filtrado[df_filtrado['NO_EXP'].astype(str).str.strip() != '-']['VL_FOB'].sum()
    importacao_total = df_filtrado[df_filtrado['NO_IMP'].astype(str).str.strip() != '-']['VL_FOB'].sum()
else:
    exportacao_total, importacao_total = 0, 0

saldo_comercial = exportacao_total - importacao_total

with col1:
    st.metric("Total Exportado (FOB)", f"US$ {exportacao_total:,.2f}")
with col2:
    st.metric("Total Importado (FOB)", f"US$ {importacao_total:,.2f}")
with col3:
    st.metric("Saldo Comercial", f"US$ {saldo_comercial:,.2f}")

# Gráficos
st.header("Top 10 Países Exportadores e Importadores")
col4, col5 = st.columns(2)

with col4:
    st.subheader("Top 10 Exportações")
    if 'NO_EXP' in df_filtrado.columns and 'NO_PAIS_DESTINO' in df_filtrado.columns:
        df_exp = df_filtrado[df_filtrado['NO_EXP'].astype(str).str.strip() != '-']
        if not df_exp.empty:
            df_top_exp = df_exp.groupby('NO_PAIS_DESTINO')['VL_FOB'].sum().nlargest(10).reset_index()
            fig_exp = px.bar(df_top_exp, x='NO_PAIS_DESTINO', y='VL_FOB',
                             title="Exportações (FOB)",
                             labels={'NO_PAIS_DESTINO': 'País Destino', 'VL_FOB': 'Valor FOB (US$)'})
            st.plotly_chart(fig_exp, use_container_width=True)
        else:
            st.info("Não há dados de exportação para o ano selecionado.")
    else:
        st.warning("Colunas de exportação não encontradas no CSV.")

with col5:
    st.subheader("Top 10 Importações")
    if 'NO_IMP' in df_filtrado.columns and 'NO_PAIS_ORIGEM' in df_filtrado.columns:
        df_imp = df_filtrado[df_filtrado['NO_IMP'].astype(str).str.strip() != '-']
        if not df_imp.empty:
            df_top_imp = df_imp.groupby('NO_PAIS_ORIGEM')['VL_FOB'].sum().nlargest(10).reset_index()
            fig_imp = px.bar(df_top_imp, x='NO_PAIS_ORIGEM', y='VL_FOB',
                             title="Importações (FOB)",
                             labels={'NO_PAIS_ORIGEM': 'País Origem', 'VL_FOB': 'Valor FOB (US$)'})
            st.plotly_chart(fig_imp, use_container_width=True)
        else:
            st.info("Não há dados de importação para o ano selecionado.")
    else:
        st.warning("Colunas de importação não encontradas no CSV.")

# Gráfico de saldo comercial anual
st.header("Saldo Comercial Anual")
if 'NO_EXP' in df_geral.columns and 'NO_IMP' in df_geral.columns:
    df_agrupado = df_geral.groupby('CO_ANO').agg(
        exportacoes=('VL_FOB', lambda x: x[df_geral.loc[x.index, 'NO_EXP'].astype(str).str.strip() != '-'].sum()),
        importacoes=('VL_FOB', lambda x: x[df_geral.loc[x.index, 'NO_IMP'].astype(str).str.strip() != '-'].sum())
    ).reset_index()

    df_agrupado['saldo'] = df_agrupado['exportacoes'] - df_agrupado['importacoes']

    fig_saldo = px.line(df_agrupado, x='CO_ANO', y='saldo',
                        title="Saldo Comercial (Exportação - Importação) ao longo dos anos")
    fig_saldo.update_traces(mode='lines+markers')
    st.plotly_chart(fig_saldo, use_container_width=True)
else:
    st.warning("Colunas necessárias para cálculo do saldo anual não encontradas.")

# Exibindo os dados brutos
st.header("Dados Brutos")
st.dataframe(df_filtrado)
