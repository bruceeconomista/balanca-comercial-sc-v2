import streamlit as st
import pandas as pd
import os
import altair as alt
import plotly.express as px
import sys
import traceback

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
            
            # Limpar os nomes das colunas (BOM: proteger caso já limpo)
            df_exp.columns = [col.replace('ï»¿', '') for col in df_exp.columns]
            df_imp.columns = [col.replace('ï»¿', '') for col in df_imp.columns]
            
            return df_exp, df_imp
        except FileNotFoundError:
            st.error("Erro: Os arquivos .parquet não foram encontrados. Certifique-se de que estão na pasta 'parquet_files'.")
            st.stop()
            return pd.DataFrame(), pd.DataFrame()

    df_exp, df_imp = load_data()

    # Combinar os dataframes para obter os anos disponíveis (somente para informação/comparação)
    if not df_exp.empty and not df_imp.empty:
        df_geral = pd.concat([df_exp, df_imp], ignore_index=True)
        anos_validos = sorted(df_geral['CO_ANO'].unique().tolist())
    elif not df_exp.empty:
        df_geral = df_exp.copy()
        anos_validos = sorted(df_exp['CO_ANO'].unique().tolist())
    elif not df_imp.empty:
        df_geral = df_imp.copy()
        anos_validos = sorted(df_imp['CO_ANO'].unique().tolist())
    else:
        df_geral = pd.DataFrame()
        anos_validos = []

    # Se quiser mostrar qual o ano mais recente (apenas informativo)
    if anos_validos:
        ano_mais_recente = anos_validos[-1]
        st.info(f"Análise usando todos os anos disponíveis. Ano mais recente no dataset: **{ano_mais_recente}**")
    else:
        st.warning("Não foi possível determinar os anos do conjunto de dados.")

    # --- 1. Filtros na Primeira Linha (removido filtro por ano) ---
    col1, col2 = st.columns(2)

    with col1:
        if not df_exp.empty:
            all_ufs = sorted(df_exp['SG_UF_NCM'].dropna().unique().tolist())
            default_ufs = ['SC'] if 'SC' in all_ufs else all_ufs
            selected_ufs = st.multiselect(
                "Selecione os Estados (UF)",
                options=all_ufs,
                default=default_ufs
            )
        else:
            selected_ufs = []

    # Observação: não existe mais widget de seleção de ano — removido intencionalmente.
    with col2:
        if anos_validos:
            st.write(f"Amostra contém anos: {', '.join(map(str, anos_validos))}")
        else:
            st.write("Sem informação de anos nos dados.")

    # Cria os dataframes filtrados para os cards, gráficos e tabelas principais
    # NOTE: removi a filtragem por CO_ANO aqui, já que você declarou que não quer filtro por ano
    if not df_exp.empty:
        if selected_ufs:
            df_exp_filtered_sc = df_exp[df_exp['SG_UF_NCM'].isin(selected_ufs)].copy()
        else:
            df_exp_filtered_sc = df_exp.copy()
    else:
        df_exp_filtered_sc = pd.DataFrame()

    if not df_imp.empty:
        if selected_ufs:
            df_imp_filtered_sc = df_imp[df_imp['SG_UF_NCM'].isin(selected_ufs)].copy()
        else:
            df_imp_filtered_sc = df_imp.copy()
    else:
        df_imp_filtered_sc = pd.DataFrame()

    # --- 2. Cards de resumo ---
    st.markdown("---")
    col3, col4, col5 = st.columns(3)

    # Cálculo dos totais (usando todos os anos, filtrados por UF se aplicado)
    total_exp = df_exp_filtered_sc['VL_FOB'].sum() if not df_exp_filtered_sc.empty else 0
    total_imp = df_imp_filtered_sc['VL_FOB'].sum() if not df_imp_filtered_sc.empty else 0
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
            "Número de produtos a exibir (exportação)", min_value=0, max_value=50, value=5, key='slider_exp'
        )
        
        if not df_exp_filtered_sc.empty and num_products_exp > 0:
            df_chart_exp = df_exp_filtered_sc.groupby(['CO_NCM', 'NO_NCM_POR'], dropna=False).agg(
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
        else:
            st.info("Não há dados de exportação para a seleção atual ou número de produtos é zero.")
            top_exp_products = []


    with col7:
        st.subheader("Produtos Mais Importados - Valor padrão = 5")
        num_products_imp = st.slider(
            "Número de produtos a exibir (importação)", min_value=0, max_value=50, value=5, key='slider_imp'
        )

        if not df_imp_filtered_sc.empty and num_products_imp > 0:
            df_chart_imp = df_imp_filtered_sc.groupby(['CO_NCM', 'NO_NCM_POR'], dropna=False).agg(
                VL_FOB=('VL_FOB', 'sum'),
                KG_LIQUIDO=('KG_LIQUIDO', 'sum')
            ).nlargest(num_products_imp, 'VL_FOB').reset_index()
            
            df_chart_imp['VL_FOB_FORMATADO'] = df_chart_imp['VL_FOB'].apply(format_value)
            
            chart_imp = alt.Chart(df_chart_imp).mark_bar().encode(
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
        else:
            st.info("Não há dados de importação para a seleção atual ou número de produtos é zero.")
            top_imp_products = []

    # --- 4. Treemaps de Países por Produto Selecionado ---
    st.markdown("---")
    st.header("TAREFA 1 - Fluxo de Exportação para os principais produtos")
    col8, col9 = st.columns(2)

    # Filtrar o DataFrame por produtos selecionados antes de agrupar para o treemap
    df_exp_filtered_products = df_exp_filtered_sc[df_exp_filtered_sc['NO_NCM_POR'].isin(top_exp_products)]
    df_imp_filtered_products = df_imp_filtered_sc[df_imp_filtered_sc['NO_NCM_POR'].isin(top_imp_products)]

    with col8:
        st.subheader("Exportações de Produtos por País")
        if not df_exp_filtered_products.empty:
            total_exp_sc = df_exp_filtered_products['VL_FOB'].sum()
            df_treemap_exp = df_exp_filtered_products.groupby('NO_PAIS', dropna=False).agg(
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
            st.info("Não há dados de exportação para a seleção atual.")

    with col9:
        st.subheader("Importações de Produtos por País")
        if not df_imp_filtered_products.empty:
            total_imp_sc = df_imp_filtered_products['VL_FOB'].sum()
            df_treemap_imp = df_imp_filtered_products.groupby('NO_PAIS', dropna=False).agg(
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
            st.info("Não há dados de importação para a seleção atual.")

    # --- TAREFA 2: Tabelas dos Maiores Países e Análise de Preço ---
    st.markdown("---")
    st.header("TAREFA 2 - Participação de cada país no total exportado / Tabela de resultados")

    col10, col11 = st.columns(2)

    # Lógica dinâmica para anos de referência (usada apenas aqui)
    anos_para_comparar_exp = sorted(df_exp['CO_ANO'].dropna().unique().tolist()) if not df_exp.empty else []
    if len(anos_para_comparar_exp) >= 2:
        anos_ref_exp = anos_para_comparar_exp[-2:]
    else:
        anos_ref_exp = anos_para_comparar_exp.copy()

    anos_para_comparar_imp = sorted(df_imp['CO_ANO'].dropna().unique().tolist()) if not df_imp.empty else []
    if len(anos_para_comparar_imp) >= 2:
        anos_ref_imp = anos_para_comparar_imp[-2:]
    else:
        anos_ref_imp = anos_para_comparar_imp.copy()

    # Tabela de exportação
    with col10:
        st.subheader("10 Maiores Destinos de Exportação / Variações Interanuais")
        if not df_exp.empty:
            # filtrar por UF se selecionado
            if selected_ufs:
                df_exp_scope = df_exp[df_exp['SG_UF_NCM'].isin(selected_ufs)].copy()
            else:
                df_exp_scope = df_exp.copy()

            if anos_ref_exp:
                df_exp_agg = df_exp_scope[df_exp_scope['CO_ANO'].isin(anos_ref_exp)]
            else:
                df_exp_agg = df_exp_scope.copy()

            if not df_exp_agg.empty:
                df_exp_agg = df_exp_agg.groupby(['CO_ANO', 'NO_PAIS'], dropna=False).agg(
                    VL_FOB=('VL_FOB', 'sum'),
                    KG_LIQUIDO=('KG_LIQUIDO', 'sum')
                ).reset_index()
                
                df_pivot = df_exp_agg.pivot_table(index='NO_PAIS', columns='CO_ANO', values=['VL_FOB', 'KG_LIQUIDO']).fillna(0)
                df_pivot.columns = [f'{metric}_{year}' for metric, year in df_pivot.columns]
                df_pivot = df_pivot.reset_index()

                for ano in anos_ref_exp:
                    if f'VL_FOB_{ano}' in df_pivot.columns and f'KG_LIQUIDO_{ano}' in df_pivot.columns:
                        df_pivot[f'Preço Médio {ano} (US$/Kg)'] = df_pivot.apply(
                            lambda row: row[f'VL_FOB_{ano}'] / row[f'KG_LIQUIDO_{ano}'] if row[f'KG_LIQUIDO_{ano}'] > 0 else 0,
                            axis=1
                        )

                # se há 2 anos, cria variação percentual entre esses dois anos (etiqueta genérica)
                if len(anos_ref_exp) == 2:
                    ano_base, ano_atual = anos_ref_exp
                    label_var = f'Var. Preço {ano_atual}/{ano_base} (%)'
                    if f'Preço Médio {ano_base} (US$/Kg)' in df_pivot.columns and f'Preço Médio {ano_atual} (US$/Kg)' in df_pivot.columns:
                        df_pivot[label_var] = df_pivot.apply(
                            lambda row: ((row[f'Preço Médio {ano_atual} (US$/Kg)'] - row[f'Preço Médio {ano_base} (US$/Kg)']) / row[f'Preço Médio {ano_base} (US$/Kg)'] * 100) if row[f'Preço Médio {ano_base} (US$/Kg)'] > 0 else 0,
                            axis=1
                        )
                else:
                    label_var = None

                # participação com base no último ano disponível na lista anos_ref_exp (se houver)
                if anos_ref_exp:
                    ultimo_ano = anos_ref_exp[-1]
                    total_fob_ultimo_ano = df_pivot.get(f'VL_FOB_{ultimo_ano}', pd.Series([0])).sum()
                    df_pivot['Participacao (%)'] = (df_pivot.get(f'VL_FOB_{ultimo_ano}', 0) / total_fob_ultimo_ano) * 100 if total_fob_ultimo_ano > 0 else 0
                else:
                    df_pivot['Participacao (%)'] = 0

                top_10_exp = df_pivot.nlargest(10, f'VL_FOB_{anos_ref_exp[-1]}' if anos_ref_exp else 'Participacao (%)').reset_index(drop=True)

                # Ajuste para renomear colunas apenas se existirem
                rename_map_exp = {}
                if 'NO_PAIS' in top_10_exp.columns:
                    rename_map_exp['NO_PAIS'] = 'País'
                if anos_ref_exp:
                    if f'VL_FOB_{anos_ref_exp[-1]}' in top_10_exp.columns:
                        rename_map_exp[f'VL_FOB_{anos_ref_exp[-1]}'] = 'Valor FOB (US$)'
                    if f'KG_LIQUIDO_{anos_ref_exp[-1]}' in top_10_exp.columns:
                        rename_map_exp[f'KG_LIQUIDO_{anos_ref_exp[-1]}'] = 'Total Kg'

                top_10_exp = top_10_exp.rename(columns=rename_map_exp)

                # Seleção segura de colunas para exibir
                columns_to_display_exp = []
                if 'País' in top_10_exp.columns:
                    columns_to_display_exp.append('País')
                if 'Valor FOB (US$)' in top_10_exp.columns:
                    columns_to_display_exp.append('Valor FOB (US$)')
                if 'Total Kg' in top_10_exp.columns:
                    columns_to_display_exp.append('Total Kg')
                if 'Participacao (%)' in top_10_exp.columns:
                    columns_to_display_exp.append('Participacao (%)')
                for ano in anos_ref_exp:
                    col_nome = f'Preço Médio {ano} (US$/Kg)'
                    if col_nome in top_10_exp.columns:
                        columns_to_display_exp.append(col_nome)
                if label_var and label_var in top_10_exp.columns:
                    columns_to_display_exp.append(label_var)

                top_10_exp_display = top_10_exp[columns_to_display_exp]

                # formatação: só inclua chaves que realmente existem
                fmt_map = {}
                if 'Valor FOB (US$)' in top_10_exp_display.columns:
                    fmt_map['Valor FOB (US$)'] = '{:,.2f}'
                if 'Total Kg' in top_10_exp_display.columns:
                    fmt_map['Total Kg'] = '{:,.0f}'
                if 'Participacao (%)' in top_10_exp_display.columns:
                    fmt_map['Participacao (%)'] = '{:.2f}%'
                for ano in anos_ref_exp:
                    col_nome = f'Preço Médio {ano} (US$/Kg)'
                    if col_nome in top_10_exp_display.columns:
                        fmt_map[col_nome] = '{:.2f}'
                if label_var and label_var in top_10_exp_display.columns:
                    fmt_map[label_var] = '{:.2f}%'

                st.dataframe(
                    top_10_exp_display.style.format(fmt_map),
                    use_container_width=True
                )
            else:
                st.info("Não há dados de exportação para os anos de referência na seleção atual.")
        else:
            st.info("Não há dados de exportação para a seleção atual.")

    # Tabela de importação (mesma lógica)
    with col11:
        st.subheader("10 Maiores Destinos de Importação / Variações Interanuais")
        if not df_imp.empty:
            if selected_ufs:
                df_imp_scope = df_imp[df_imp['SG_UF_NCM'].isin(selected_ufs)].copy()
            else:
                df_imp_scope = df_imp.copy()

            if anos_ref_imp:
                df_imp_agg = df_imp_scope[df_imp_scope['CO_ANO'].isin(anos_ref_imp)]
            else:
                df_imp_agg = df_imp_scope.copy()

            if not df_imp_agg.empty:
                df_imp_agg = df_imp_agg.groupby(['CO_ANO', 'NO_PAIS'], dropna=False).agg(
                    VL_FOB=('VL_FOB', 'sum'),
                    KG_LIQUIDO=('KG_LIQUIDO', 'sum')
                ).reset_index()

                df_imp_pivot = df_imp_agg.pivot_table(index='NO_PAIS', columns='CO_ANO', values=['VL_FOB', 'KG_LIQUIDO']).fillna(0)
                df_imp_pivot.columns = [f'{metric}_{year}' for metric, year in df_imp_pivot.columns]
                df_imp_pivot = df_imp_pivot.reset_index()

                for ano in anos_ref_imp:
                    if f'VL_FOB_{ano}' in df_imp_pivot.columns and f'KG_LIQUIDO_{ano}' in df_imp_pivot.columns:
                        df_imp_pivot[f'Preço Médio {ano} (US$/Kg)'] = df_imp_pivot.apply(
                            lambda row: row[f'VL_FOB_{ano}'] / row[f'KG_LIQUIDO_{ano}'] if row[f'KG_LIQUIDO_{ano}'] > 0 else 0,
                            axis=1
                        )

                if len(anos_ref_imp) == 2:
                    ano_base, ano_atual = anos_ref_imp
                    label_var_imp = f'Var. Preço {ano_atual}/{ano_base} (%)'
                    if f'Preço Médio {ano_base} (US$/Kg)' in df_imp_pivot.columns and f'Preço Médio {ano_atual} (US$/Kg)' in df_imp_pivot.columns:
                        df_imp_pivot[label_var_imp] = df_imp_pivot.apply(
                            lambda row: ((row[f'Preço Médio {ano_atual} (US$/Kg)'] - row[f'Preço Médio {ano_base} (US$/Kg)']) / row[f'Preço Médio {ano_base} (US$/Kg)'] * 100) if row[f'Preço Médio {ano_base} (US$/Kg)'] > 0 else 0,
                            axis=1
                        )
                else:
                    label_var_imp = None

                if anos_ref_imp:
                    ultimo_ano_imp = anos_ref_imp[-1]
                    total_imp_ultimo_ano = df_imp_pivot.get(f'VL_FOB_{ultimo_ano_imp}', pd.Series([0])).sum()
                    df_imp_pivot['Participacao (%)'] = (df_imp_pivot.get(f'VL_FOB_{ultimo_ano_imp}', 0) / total_imp_ultimo_ano) * 100 if total_imp_ultimo_ano > 0 else 0
                else:
                    df_imp_pivot['Participacao (%)'] = 0

                top_10_imp = df_imp_pivot.nlargest(10, f'VL_FOB_{anos_ref_imp[-1]}' if anos_ref_imp else 'Participacao (%)').reset_index(drop=True)

                # renomeação segura
                rename_map_imp = {}
                if 'NO_PAIS' in top_10_imp.columns:
                    rename_map_imp['NO_PAIS'] = 'País'
                if anos_ref_imp:
                    if f'VL_FOB_{anos_ref_imp[-1]}' in top_10_imp.columns:
                        rename_map_imp[f'VL_FOB_{anos_ref_imp[-1]}'] = 'Valor FOB (US$)'
                    if f'KG_LIQUIDO_{anos_ref_imp[-1]}' in top_10_imp.columns:
                        rename_map_imp[f'KG_LIQUIDO_{anos_ref_imp[-1]}'] = 'Total Kg'

                top_10_imp = top_10_imp.rename(columns=rename_map_imp)

                columns_to_display_imp = []
                if 'País' in top_10_imp.columns:
                    columns_to_display_imp.append('País')
                if 'Valor FOB (US$)' in top_10_imp.columns:
                    columns_to_display_imp.append('Valor FOB (US$)')
                if 'Total Kg' in top_10_imp.columns:
                    columns_to_display_imp.append('Total Kg')
                if 'Participacao (%)' in top_10_imp.columns:
                    columns_to_display_imp.append('Participacao (%)')
                for ano in anos_ref_imp:
                    col_nome = f'Preço Médio {ano} (US$/Kg)'
                    if col_nome in top_10_imp.columns:
                        columns_to_display_imp.append(col_nome)
                if label_var_imp and label_var_imp in top_10_imp.columns:
                    columns_to_display_imp.append(label_var_imp)

                top_10_imp_display = top_10_imp[columns_to_display_imp]

                fmt_map_imp = {}
                if 'Valor FOB (US$)' in top_10_imp_display.columns:
                    fmt_map_imp['Valor FOB (US$)'] = '{:,.2f}'
                if 'Total Kg' in top_10_imp_display.columns:
                    fmt_map_imp['Total Kg'] = '{:,.0f}'
                if 'Participacao (%)' in top_10_imp_display.columns:
                    fmt_map_imp['Participacao (%)'] = '{:.2f}%'
                for ano in anos_ref_imp:
                    col_nome = f'Preço Médio {ano} (US$/Kg)'
                    if col_nome in top_10_imp_display.columns:
                        fmt_map_imp[col_nome] = '{:.2f}'
                if label_var_imp and label_var_imp in top_10_imp_display.columns:
                    fmt_map_imp[label_var_imp] = '{:.2f}%'

                st.dataframe(
                    top_10_imp_display.style.format(fmt_map_imp),
                    use_container_width=True
                )
            else:
                st.info("Não há dados de importação para os anos de referência na seleção atual.")
        else:
            st.info("Não há dados de importação para a seleção atual.")

    # --- 6. Treemaps de Países (Visão Geral) ---
    st.markdown("---")
    st.header("TAREFA 2 - Análise de Países por Total Geral de Comércio")
    col12, col13 = st.columns(2)

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

except Exception as e:
    st.error("Ocorreu um erro inesperado ao executar o aplicativo. Por favor, entre em contato com o administrador.")
    st.write("---")
    st.header("Detalhes Técnicos do Erro")
    st.exception(e)
    st.write("---")
    st.text("Detalhes do Traceback:")
    st.code(traceback.format_exc())
    st.stop()
