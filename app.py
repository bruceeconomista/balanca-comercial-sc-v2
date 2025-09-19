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

# Nomes dos arquivos
EXP_FILE = "EXP_TOTAL.parquet"
IMP_FILE = "IMP_TOTAL.parquet"
PARQUET_FOLDER = "parquet_files"

@st.cache_data
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
        
        # Correção da codificação de caracteres
        for df in [df_exp, df_imp]:
            if 'NO_NCM_POR' in df.columns:
                df['NO_NCM_POR'] = df['NO_NCM_POR'].str.encode('latin1').str.decode('utf8', 'ignore')
            if 'NO_PAIS' in df.columns:
                df['NO_PAIS'] = df['NO_PAIS'].str.encode('latin1').str.decode('utf8', 'ignore')
        
        return df_exp, df_imp
    except FileNotFoundError:
        st.error("Erro: Os arquivos .parquet não foram encontrados. Certifique-se de que estão na pasta 'parquet_files'.")
        st.stop() # Interrompe a execução do script para evitar o KeyError
    except Exception as e:
        st.error(f"Erro ao carregar os dados: {e}")
        st.stop() # Interrompe a execução para qualquer outro erro

df_exp, df_imp = load_data()

# O restante do código abaixo não precisa ser alterado, pois ele já está funcionando corretamente.

# --- 1. Filtros na Primeira Linha ---
col1, col2 = st.columns(2)

with col1:
    all_ufs = sorted(df_exp['SG_UF_NCM'].unique().tolist()) if 'SG_UF_NCM' in df_exp.columns else []
    default_ufs = ['SC'] if 'SC' in all_ufs else all_ufs
    selected_ufs = st.multiselect(
        "Selecione os Estados (UF)",
        options=all_ufs,
        default=default_ufs
    )

with col2:
    all_years = sorted(df_exp['CO_ANO'].unique().tolist(), reverse=True) if 'CO_ANO' in df_exp.columns else []
    selected_year = st.selectbox(
        "Selecione o Ano",
        options=all_years,
        index=0 if all_years else None
    )

# --- 2. Cards de resumo ---
st.markdown("---")
col3, col4, col5 = st.columns(3)

# Cria os dataframes filtrados para os cards, gráficos e tabelas principais
df_exp_filtered = df_exp[
    (df_exp['CO_ANO'] == selected_year) &
    (df_exp['SG_UF_NCM'].isin(selected_ufs))
]

df_imp_filtered = df_imp[
    (df_imp['CO_ANO'] == selected_year) &
    (df_imp['SG_UF_NCM'].isin(selected_ufs))
]

# Cálculo dos totais
total_exp = df_exp_filtered['VL_FOB'].sum()
total_imp = df_imp_filtered['VL_FOB'].sum()
balanca_comercial = total_exp - total_imp

# Funções de formatação
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

# TAREFA 1: Produtos Mais Exportados
with col6:
    st.subheader("TAREFA 1 - Produtos Mais Exportados")
    num_products_exp = st.slider(
        "Número de produtos a exibir", min_value=0, max_value=20, value=5, key='slider_exp'
    )
    
    df_chart_exp = df_exp_filtered.groupby(['CO_NCM', 'NO_NCM_POR']).agg(
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
        df_exp_agg = df_exp[(df_exp['CO_ANO'].isin([selected_year-1, selected_year])) & (df_exp['SG_UF_NCM'].isin(selected_ufs))]
        df_exp_agg = df_exp_agg.groupby(['CO_ANO', 'CO_NCM', 'NO_NCM_POR']).agg(
            VL_FOB=('VL_FOB', 'sum'),
            KG_LIQUIDO=('KG_LIQUIDO', 'sum')
        ).reset_index()

        df_exp_pivot = df_exp_agg.pivot_table(
            index=['CO_NCM', 'NO_NCM_POR'],
            columns='CO_ANO',
            values=['VL_FOB', 'KG_LIQUIDO']
        ).fillna(0)
        df_exp_pivot.columns = [f'{metric}_{year}' for metric, year in df_exp_pivot.columns]
        df_exp_pivot = df_exp_pivot.reset_index()
        
        df_exp_pivot = df_exp_pivot[df_exp_pivot['NO_NCM_POR'].isin(top_exp_products)]

        total_fob_selected_year = df_exp_pivot[f'VL_FOB_{selected_year}'].sum()
        df_exp_pivot['Participacao (%)'] = (df_exp_pivot[f'VL_FOB_{selected_year}'] / total_fob_selected_year) * 100 if total_fob_selected_year > 0 else 0
        
        if f'VL_FOB_{selected_year-1}' in df_exp_pivot.columns and f'KG_LIQUIDO_{selected_year-1}' in df_exp_pivot.columns:
            df_exp_pivot[f'Preço médio {selected_year-1} (US$/Kg)'] = df_exp_pivot.apply(
                lambda row: row[f'VL_FOB_{selected_year-1}'] / row[f'KG_LIQUIDO_{selected_year-1}'] if row[f'KG_LIQUIDO_{selected_year-1}'] > 0 else 0, axis=1
            )
            df_exp_pivot[f'Preço médio {selected_year} (US$/Kg)'] = df_exp_pivot.apply(
                lambda row: row[f'VL_FOB_{selected_year}'] / row[f'KG_LIQUIDO_{selected_year}'] if row[f'KG_LIQUIDO_{selected_year}'] > 0 else 0, axis=1
            )
            df_exp_pivot[f'Variação Preço {selected_year}/{selected_year-1} (%)'] = df_exp_pivot.apply(
                lambda row: ((row[f'Preço médio {selected_year} (US$/Kg)'] - row[f'Preço médio {selected_year-1} (US$/Kg)']) / row[f'Preço médio {selected_year-1} (US$/Kg)'] * 100) if row[f'Preço médio {selected_year-1} (US$/Kg)'] > 0 else 0, axis=1
            )
        else:
            df_exp_pivot[f'Preço médio {selected_year-1} (US$/Kg)'] = 0
            df_exp_pivot[f'Preço médio {selected_year} (US$/Kg)'] = 0
            df_exp_pivot[f'Variação Preço {selected_year}/{selected_year-1} (%)'] = 0
        
        df_exp_display = df_exp_pivot.rename(columns={
            'CO_NCM': 'NCM',
            'NO_NCM_POR': 'Produto',
            f'VL_FOB_{selected_year}': 'Valor FOB',
            f'KG_LIQUIDO_{selected_year}': 'Total KG'
        })
        
        st.subheader(f"Dados dos {num_products_exp} Produtos Mais Exportados")
        st.dataframe(
            df_exp_display[[
                'NCM', 'Produto', 'Valor FOB', 'Total KG', 'Participacao (%)',
                f'Preço médio {selected_year-1} (US$/Kg)', f'Preço médio {selected_year} (US$/Kg)',
                f'Variação Preço {selected_year}/{selected_year-1} (%)'
            ]].style.format({
                'Valor FOB': lambda x: format_brl(x, 2),
                'Total KG': lambda x: format_brl(x, 0),
                'Participacao (%)': '{:.2f}%',
                f'Preço médio {selected_year-1} (US$/Kg)': '{:.2f}',
                f'Preço médio {selected_year} (US$/Kg)': '{:.2f}',
                f'Variação Preço {selected_year}/{selected_year-1} (%)': '{:.2f}%'
            }),
            use_container_width=True,
            hide_index=True
        )


# TAREFA 1: Produtos Mais Importados
with col7:
    st.subheader("Produtos Mais Importados")
    num_products_imp = st.slider(
        "Número de produtos a exibir", min_value=0, max_value=20, value=5, key='slider_imp'
    )

    df_chart_imp = df_imp_filtered.groupby(['CO_NCM', 'NO_NCM_POR']).agg(
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
        df_imp_agg = df_imp[(df_imp['CO_ANO'].isin([selected_year-1, selected_year])) & (df_imp['SG_UF_NCM'].isin(selected_ufs))]
        df_imp_agg = df_imp_agg.groupby(['CO_ANO', 'CO_NCM', 'NO_NCM_POR']).agg(
            VL_FOB=('VL_FOB', 'sum'),
            KG_LIQUIDO=('KG_LIQUIDO', 'sum')
        ).reset_index()
        
        df_imp_pivot = df_imp_agg.pivot_table(
            index=['CO_NCM', 'NO_NCM_POR'],
            columns='CO_ANO',
            values=['VL_FOB', 'KG_LIQUIDO']
        ).fillna(0)
        df_imp_pivot.columns = [f'{metric}_{year}' for metric, year in df_imp_pivot.columns]
        df_imp_pivot = df_imp_pivot.reset_index()
        
        df_imp_pivot = df_imp_pivot[df_imp_pivot['NO_NCM_POR'].isin(top_imp_products)]
        
        total_fob_selected_year = df_imp_pivot[f'VL_FOB_{selected_year}'].sum()
        df_imp_pivot['Participacao (%)'] = (df_imp_pivot[f'VL_FOB_{selected_year}'] / total_fob_selected_year) * 100 if total_fob_selected_year > 0 else 0
        
        if f'VL_FOB_{selected_year-1}' in df_imp_pivot.columns and f'KG_LIQUIDO_{selected_year-1}' in df_imp_pivot.columns:
            df_imp_pivot[f'Preço médio {selected_year-1} (US$/Kg)'] = df_imp_pivot.apply(
                lambda row: row[f'VL_FOB_{selected_year-1}'] / row[f'KG_LIQUIDO_{selected_year-1}'] if row[f'KG_LIQUIDO_{selected_year-1}'] > 0 else 0, axis=1
            )
            df_imp_pivot[f'Preço médio {selected_year} (US$/Kg)'] = df_imp_pivot.apply(
                lambda row: row[f'VL_FOB_{selected_year}'] / row[f'KG_LIQUIDO_{selected_year}'] if row[f'KG_LIQUIDO_{selected_year}'] > 0 else 0, axis=1
            )
            df_imp_pivot[f'Variação Preço {selected_year}/{selected_year-1} (%)'] = df_imp_pivot.apply(
                lambda row: ((row[f'Preço médio {selected_year} (US$/Kg)'] - row[f'Preço médio {selected_year-1} (US$/Kg)']) / row[f'Preço médio {selected_year-1} (US$/Kg)'] * 100) if row[f'Preço médio {selected_year-1} (US$/Kg)'] > 0 else 0, axis=1
            )
        else:
            df_imp_pivot[f'Preço médio {selected_year-1} (US$/Kg)'] = 0
            df_imp_pivot[f'Preço médio {selected_year} (US$/Kg)'] = 0
            df_imp_pivot[f'Variação Preço {selected_year}/{selected_year-1} (%)'] = 0
        
        df_imp_display = df_imp_pivot.rename(columns={
            'CO_NCM': 'NCM',
            'NO_NCM_POR': 'Produto',
            f'VL_FOB_{selected_year}': 'Valor FOB',
            f'KG_LIQUIDO_{selected_year}': 'Total KG'
        })
        
        st.subheader(f"Dados dos {num_products_imp} Produtos Mais Importados")
        st.dataframe(
            df_imp_display[[
                'NCM', 'Produto', 'Valor FOB', 'Total KG', 'Participacao (%)',
                f'Preço médio {selected_year-1} (US$/Kg)', f'Preço médio {selected_year} (US$/Kg)',
                f'Variação Preço {selected_year}/{selected_year-1} (%)'
            ]].style.format({
                'Valor FOB': lambda x: format_brl(x, 2),
                'Total KG': lambda x: format_brl(x, 0),
                'Participacao (%)': '{:.2f}%',
                f'Preço médio {selected_year-1} (US$/Kg)': '{:.2f}',
                f'Preço médio {selected_year} (US$/Kg)': '{:.2f}',
                f'Variação Preço {selected_year}/{selected_year-1} (%)': '{:.2f}%'
            }),
            use_container_width=True,
            hide_index=True
        )


# --- 4. Treemaps de Países por Produto Selecionado ---
st.markdown("---")
st.header("TAREFA 1 - Fluxo de Exportação e Importação por País (Principais Produtos)")
col8, col9 = st.columns(2)

df_exp_filtered_products = df_exp_filtered[df_exp_filtered['NO_NCM_POR'].isin(top_exp_products)]
df_imp_filtered_products = df_imp_filtered[df_imp_filtered['NO_NCM_POR'].isin(top_imp_products)]

with col8:
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
## Tarefa 2: Análise de Parceiros Comerciais e Competitividade Geral
# ---
# --- 5. Tabelas dos Maiores Países e Análise de Preço ---
st.markdown("---")
st.header("TAREFA 2 - Participação de cada país no total exportado / Tabela de resultados")

col10, col11 = st.columns(2)

with col10:
    st.subheader(f"Destinos de Exportação / Variações Interanuais ({selected_year} vs {selected_year-1})")
    if not df_exp_filtered.empty:
        df_exp_agg = df_exp[(df_exp['CO_ANO'].isin([selected_year-1, selected_year])) & (df_exp['SG_UF_NCM'].isin(selected_ufs))]
        df_exp_agg = df_exp_agg.groupby(['CO_ANO', 'NO_PAIS']).agg(
            VL_FOB=('VL_FOB', 'sum'),
            KG_LIQUIDO=('KG_LIQUIDO', 'sum')
        ).reset_index()
        
        df_pivot = df_exp_agg.pivot_table(index='NO_PAIS', columns='CO_ANO', values=['VL_FOB', 'KG_LIQUIDO']).fillna(0)
        df_pivot.columns = [f'{metric}_{year}' for metric, year in df_pivot.columns]
        df_pivot = df_pivot.reset_index()

        if f'VL_FOB_{selected_year-1}' in df_pivot.columns and f'KG_LIQUIDO_{selected_year-1}' in df_pivot.columns:
            df_pivot[f'Preço Médio {selected_year-1} (US$/Kg)'] = df_pivot.apply(
                lambda row: row[f'VL_FOB_{selected_year-1}'] / row[f'KG_LIQUIDO_{selected_year-1}'] if row[f'KG_LIQUIDO_{selected_year-1}'] > 0 else 0, axis=1
            )
            df_pivot[f'Preço Médio {selected_year} (US$/Kg)'] = df_pivot.apply(
                lambda row: row[f'VL_FOB_{selected_year}'] / row[f'KG_LIQUIDO_{selected_year}'] if row[f'KG_LIQUIDO_{selected_year}'] > 0 else 0, axis=1
            )
            df_pivot[f'Var. Preço {selected_year}/{selected_year-1} (%)'] = df_pivot.apply(
                lambda row: ((row[f'Preço Médio {selected_year} (US$/Kg)'] - row[f'Preço Médio {selected_year-1} (US$/Kg)']) / row[f'Preço Médio {selected_year-1} (US$/Kg)'] * 100) if row[f'Preço Médio {selected_year-1} (US$/Kg)'] > 0 else 0, axis=1
            )
        else:
            df_pivot[f'Preço Médio {selected_year-1} (US$/Kg)'] = 0
            df_pivot[f'Preço Médio {selected_year} (US$/Kg)'] = 0
            df_pivot[f'Var. Preço {selected_year}/{selected_year-1} (%)'] = 0
        
        total_fob_selected_year = df_pivot[f'VL_FOB_{selected_year}'].sum()
        df_pivot['Participacao (%)'] = (df_pivot[f'VL_FOB_{selected_year}'] / total_fob_selected_year) * 100 if total_fob_selected_year > 0 else 0
        
        df_pivot_sorted = df_pivot.sort_values(by=f'VL_FOB_{selected_year}', ascending=False).reset_index(drop=True)
        top_10_exp = df_pivot_sorted.rename(columns={
            'NO_PAIS': 'País',
            f'VL_FOB_{selected_year}': 'Valor FOB (US$)',
            f'KG_LIQUIDO_{selected_year}': 'Total Kg'
        })
        
        top_10_exp_display = top_10_exp[['País', 'Valor FOB (US$)', 'Total Kg', 'Participacao (%)', f'Preço Médio {selected_year-1} (US$/Kg)', f'Preço Médio {selected_year} (US$/Kg)', f'Var. Preço {selected_year}/{selected_year-1} (%)']]

        st.dataframe(
            top_10_exp_display.style.format({
                'Valor FOB (US$)': lambda x: format_brl(x, 2),
                'Total Kg': lambda x: format_brl(x, 0),
                'Participacao (%)': '{:.2f}%',
                f'Preço Médio {selected_year-1} (US$/Kg)': '{:.2f}',
                f'Preço Médio {selected_year} (US$/Kg)': '{:.2f}',
                f'Var. Preço {selected_year}/{selected_year-1} (%)': '{:.2f}%',
            }),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("Não há dados de exportação para a seleção atual.")


with col11:
    st.subheader(f"Origens de Importação / Variações Interanuais ({selected_year} vs {selected_year-1})")
    if not df_imp_filtered.empty:
        df_imp_agg = df_imp[(df_imp['CO_ANO'].isin([selected_year-1, selected_year])) & (df_imp['SG_UF_NCM'].isin(selected_ufs))]
        df_imp_agg = df_imp_agg.groupby(['CO_ANO', 'NO_PAIS']).agg(
            VL_FOB=('VL_FOB', 'sum'),
            KG_LIQUIDO=('KG_LIQUIDO', 'sum')
        ).reset_index()

        df_imp_pivot = df_imp_agg.pivot_table(index='NO_PAIS', columns='CO_ANO', values=['VL_FOB', 'KG_LIQUIDO']).fillna(0)
        df_imp_pivot.columns = [f'{metric}_{year}' for metric, year in df_imp_pivot.columns]
        df_imp_pivot = df_imp_pivot.reset_index()

        if f'VL_FOB_{selected_year-1}' in df_imp_pivot.columns and f'KG_LIQUIDO_{selected_year-1}' in df_imp_pivot.columns:
            df_imp_pivot[f'Preço Médio {selected_year-1} (US$/Kg)'] = df_imp_pivot.apply(
                lambda row: row[f'VL_FOB_{selected_year-1}'] / row[f'KG_LIQUIDO_{selected_year-1}'] if row[f'KG_LIQUIDO_{selected_year-1}'] > 0 else 0, axis=1
            )
            df_imp_pivot[f'Preço Médio {selected_year} (US$/Kg)'] = df_imp_pivot.apply(
                lambda row: row[f'VL_FOB_{selected_year}'] / row[f'KG_LIQUIDO_{selected_year}'] if row[f'KG_LIQUIDO_{selected_year}'] > 0 else 0, axis=1
            )
            df_imp_pivot[f'Var. Preço {selected_year}/{selected_year-1} (%)'] = df_imp_pivot.apply(
                lambda row: ((row[f'Preço Médio {selected_year} (US$/Kg)'] - row[f'Preço Médio {selected_year-1} (US$/Kg)']) / row[f'Preço Médio {selected_year-1} (US$/Kg)'] * 100) if row[f'Preço Médio {selected_year-1} (US$/Kg)'] > 0 else 0, axis=1
            )
        else:
            df_imp_pivot[f'Preço Médio {selected_year-1} (US$/Kg)'] = 0
            df_imp_pivot[f'Preço Médio {selected_year} (US$/Kg)'] = 0
            df_imp_pivot[f'Var. Preço {selected_year}/{selected_year-1} (%)'] = 0
        
        total_imp_selected_year = df_imp_pivot[f'VL_FOB_{selected_year}'].sum()
        df_imp_pivot['Participacao (%)'] = (df_imp_pivot[f'VL_FOB_{selected_year}'] / total_imp_selected_year) * 100 if total_imp_selected_year > 0 else 0

        df_imp_pivot_sorted = df_imp_pivot.sort_values(by=f'VL_FOB_{selected_year}', ascending=False).reset_index(drop=True)
        top_10_imp = df_imp_pivot_sorted.rename(columns={
            'NO_PAIS': 'País',
            f'VL_FOB_{selected_year}': 'Valor FOB (US$)',
            f'KG_LIQUIDO_{selected_year}': 'Total Kg'
        })
        
        top_10_imp_display = top_10_imp[['País', 'Valor FOB (US$)', 'Total Kg', 'Participacao (%)', f'Preço Médio {selected_year-1} (US$/Kg)', f'Preço Médio {selected_year} (US$/Kg)', f'Var. Preço {selected_year}/{selected_year-1} (%)']]
        
        st.dataframe(
            top_10_imp_display.style.format({
                'Valor FOB (US$)': lambda x: format_brl(x, 2),
                'Total Kg': lambda x: format_brl(x, 0),
                'Participacao (%)': '{:.2f}%',
                f'Preço Médio {selected_year-1} (US$/Kg)': '{:.2f}',
                f'Preço Médio {selected_year} (US$/Kg)': '{:.2f}',
                f'Var. Preço {selected_year}/{selected_year-1} (%)': '{:.2f}%',
            }),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("Não há dados de importação para a seleção atual.")

# --- 6. Treemaps de Países (Visão Geral) ---
st.markdown("---")
st.header("TAREFA 2 - Análise de Países por Total Geral de Comércio")
col12, col13 = st.columns(2)

with col12:
    st.subheader(f"Exportações (Total Geral) ({selected_year})")
    df_exp_geral = df_exp_filtered.groupby('NO_PAIS').agg(
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

with col13:
    st.subheader(f"Importações (Total Geral) ({selected_year})")
    df_imp_geral = df_imp_filtered.groupby('NO_PAIS').agg(
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
