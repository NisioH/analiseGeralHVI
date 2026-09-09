import streamlit as st
import pandas as pd
import plotly.express as px
import streamlit.components.v1 as components

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Dashboard HVI", layout="wide", page_icon="🌱")
st.title("Análise de Qualidade do Algodão (HVI) 🌱")
st.markdown("Acompanhamento de safra: Variedade, Tipo Visual e Índices de Qualidade.")


# --- INGESTÃO E LIMPEZA DE DADOS AUTOMÁTICA ---
@st.cache_data
def carregar_dados():
    df = pd.read_excel('RetornoHVI_Geral1.xlsx')

    df.columns = df.iloc[2]
    df = df.drop([0, 1, 2]).reset_index(drop=True)

    colunas_uteis = ['Fardo', 'Variedade', 'Talhão', 'Mic', 'Res', 'Uhm', 'Tp.V.']
    df = df[colunas_uteis].copy()

    df['Mic'] = df['Mic'].astype(str).str.replace(',', '.').astype(float)
    df['Res'] = df['Res'].astype(str).str.replace(',', '.').astype(float)
    df['Uhm'] = df['Uhm'].astype(str).str.replace(',', '.').astype(float)

    limites = [0, 1.04, 1.07, 1.10, 1.13, 1.17, 1.20, 1.23, 1.26, 1.29, 1.32]
    valores_un = ['33', '34', '35', '36', '37', '38', '39', '40', '41', '42']
    df['UN'] = pd.cut(df['Uhm'], bins=limites, labels=valores_un)

    df['Mic_fora_padrao'] = ~df['Mic'].between(3.5, 4.9, inclusive='both')
    df['baixa_resistencia'] = ~df['Res'].between(28, 35, inclusive='both')

    return df


try:
    df = carregar_dados()
except Exception as e:
    st.error("Erro ao carregar os dados. Verifique se o arquivo 'RetornoHVI_Geral.xlsx' bruto está na mesma pasta.")
    st.stop()

# --- INTERFACE COM ABAS ---
aba1, aba2, aba3, aba4 = st.tabs([
    "🍕 1. Visão Geral (Variedades)",
    "📊 2. Produção (Tabela Excel)",
    "⚠️ 3. Alertas de Qualidade",
    "⚖️ 4. Comparador de Perfis"
])

# ABA 1 - Gráfico de Pizza
with aba1:
    st.subheader("Proporção Total de Fardos por Variedade")
    contagem_var = df['Variedade'].value_counts().reset_index()
    contagem_var.columns = ['Variedade', 'Quantidade']

    fig_pizza = px.pie(contagem_var, values='Quantidade', names='Variedade', hole=0.3)
    fig_pizza.update_traces(textposition='inside', textinfo='percent+label')
    st.plotly_chart(fig_pizza, use_container_width=True)

# ABA 2 - Produção Detalhada (Matriz Estilo Excel)
with aba2:
    st.subheader("Resumo Geral: Produção por Tipo Visual (Tp.V.) e Fibra (UN)")

    variedade_filtro = st.selectbox("Selecione a Variedade que deseja analisar:", df['Variedade'].unique())
    df_filtrado = df[df['Variedade'] == variedade_filtro]

    if not df_filtrado.empty:
        tabela_matriz = pd.crosstab(
            index=df_filtrado['Tp.V.'],
            columns=df_filtrado['UN'],
            margins=True,
            margins_name='TOTAL TIPO'
        )

        tabela_matriz = tabela_matriz.loc[:, (tabela_matriz != 0).any(axis=0)]
        tabela_matriz = tabela_matriz.replace(0, "")
        tabela_matriz.columns = [f"FIBRA {c}" if c != 'TOTAL TIPO' else c for c in tabela_matriz.columns]
        tabela_matriz.index.name = "TIPO"

        # HTML blindado com suporte a scroll no celular
        html_completo = f"""
        <!DOCTYPE html>
        <html>
        <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{
                font-family: Arial, sans-serif;
                background-color: transparent;
                margin: 0;
                padding: 0;
            }}
            .container {{
                overflow-x: auto;
                width: 100%;
            }}
            .tabela-excel {{
                border-collapse: collapse;
                font-size: 14px;
                width: 100%;
                color: black;
                background-color: white;
            }}
            .tabela-excel th, .tabela-excel td {{
                border: 1px solid #7f8c8d;
                padding: 8px;
                text-align: center;
                min-width: 45px;
            }}
            .tabela-excel thead th {{ background-color: #b2ebf2; }}
            .tabela-excel tbody th {{ background-color: #e0f7fa; }}
            .tabela-excel td:last-child, .tabela-excel th:last-child {{ background-color: #4dd0e1; font-weight: bold; }}
            .tabela-excel tbody tr:last-child th, .tabela-excel tbody tr:last-child td {{ background-color: #80deea; font-weight: bold; }}
        </style>
        </head>
        <body>
            <div class="container">
                {tabela_matriz.to_html(classes="tabela-excel", border=0)}
            </div>
        </body>
        </html>
        """

        components.html(html_completo, height=600, scrolling=True)
    else:
        st.info("Nenhum dado encontrado para esta variedade.")

# ABA 3 - Alertas de Qualidade
with aba3:
    st.subheader("Monitoramento de Amostras Fora do Padrão")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**🔴 Micronaire Fora do Padrão (< 3.5 ou > 4.9)**")
        df_mic = df[df['Mic_fora_padrao'] == True]
        if not df_mic.empty:
            fig_mic = px.histogram(df_mic, x='Variedade', color='Variedade', text_auto=True)
            fig_mic.update_layout(showlegend=False, yaxis_title="Fardos Afetados", xaxis_title="")
            st.plotly_chart(fig_mic, use_container_width=True)
        else:
            st.success("Tudo certo! Nenhuma amostra fora do padrão de Micronaire.")

    with col2:
        st.markdown("**🟡 Baixa Resistência (< 28)**")
        df_res = df[df['baixa_resistencia'] == True]
        if not df_res.empty:
            fig_res = px.histogram(df_res, x='Variedade', color='Variedade', text_auto=True)
            fig_res.update_layout(showlegend=False, yaxis_title="Fardos Afetados", xaxis_title="")
            st.plotly_chart(fig_res, use_container_width=True)
        else:
            st.success("Tudo certo! Nenhuma amostra com baixa resistência.")

# ABA 4 - Comparador Direto por Tipo Visual
with aba4:
    st.subheader("Batalha de Variedades por Tipo Visual")
    st.markdown("Selecione um Tipo Visual para comparar o comprimento de fibra (UN) de cada variedade.")

    tipos_visuais_disponiveis = sorted(df['Tp.V.'].dropna().unique())
    tpv_selecionado = st.selectbox("Escolha o Tipo Visual (Ex: 31-3):", tipos_visuais_disponiveis)

    df_tpv = df[df['Tp.V.'] == tpv_selecionado]
    total_plumas = len(df_tpv)

    st.markdown(f"### Tipo Visual {tpv_selecionado} = {total_plumas} plumas")

    variedades_presentes = df_tpv['Variedade'].unique()

    if len(variedades_presentes) > 0:
        colunas = st.columns(len(variedades_presentes))
        cores = ['#1f77b4', '#d62728', '#2ca02c', '#ff7f0e']

        for idx, var in enumerate(variedades_presentes):
            with colunas[idx]:
                df_var = df_tpv[df_tpv['Variedade'] == var]
                total_var = len(df_var)

                st.markdown(
                    f"<h5 style='text-align: center; color: {cores[idx % len(cores)]};'>Variedade: {var} = {total_var} plumas</h5>",
                    unsafe_allow_html=True)

                df_grafico = df_var.groupby('UN', observed=True).size().reset_index(name='Quantidade')
                df_grafico = df_grafico[df_grafico['Quantidade'] > 0]

                if not df_grafico.empty:
                    fig = px.bar(
                        df_grafico,
                        x='UN',
                        y='Quantidade',
                        text_auto=True,
                        labels={'UN': 'Comprimento (UN)', 'Quantidade': 'Fardos'}
                    )
                    fig.update_traces(marker_color=cores[idx % len(cores)], textposition='outside')
                    fig.update_layout(
                        xaxis_type='category',
                        showlegend=False,
                        yaxis=dict(range=[0, df_tpv.groupby(['Variedade', 'UN'], observed=True).size().max() * 1.1])
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info(f"Sem fardos da variedade {var} neste tipo.")
    else:
        st.warning(f"Não há dados para o Tipo Visual {tpv_selecionado}.")