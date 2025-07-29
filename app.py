import streamlit as st
import pandas as pd
import plotly.express as px
import locale

# --- Configurações Iniciais ---
#locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')  # para nomes de meses em português

st.set_page_config(
    page_title="Dashboard Ouvidoria ANVISA",
    page_icon="📊",
    layout="wide"
)

# --- Funções de Carregamento de Dados ---

@st.cache_data
def carregar_dados_pesquisa():
    try:
        df = pd.read_csv("pesquisa.csv", sep=";", encoding='utf-8')
        coluna_satisfacao = "Você está satisfeito(a) com o atendimento prestado?"
        if coluna_satisfacao in df.columns:
            df[coluna_satisfacao] = df[coluna_satisfacao].str.replace('?? ', '', regex=False).str.strip()

        opcoes_coluna_data = ['Resposta à Pesquisa', 'Resposta à pesquisa']
        coluna_data_encontrada = None
        for coluna in opcoes_coluna_data:
            if coluna in df.columns:
                coluna_data_encontrada = coluna
                break
        if coluna_data_encontrada:
            df[coluna_data_encontrada] = df[coluna_data_encontrada].astype(str).str.strip()
            df[coluna_data_encontrada] = pd.to_datetime(df[coluna_data_encontrada], errors='coerce', dayfirst=True)
            df["mês"] = df[coluna_data_encontrada].dt.to_period('M')
        return df
    except FileNotFoundError:
        st.error("Arquivo 'pesquisa.csv' não encontrado.")
        return None

@st.cache_data
def carregar_dados_manifestacoes():
    try:
        df = pd.read_csv("ListaManifestacoes.csv", sep=";", encoding='utf-8')

        if 'Data de Abertura' in df.columns:
            df['Data de Abertura'] = df['Data de Abertura'].astype(str).str.strip()
            df['Data de Abertura'] = df['Data de Abertura'].replace(
                ["", " ", "null", "nan", "sem data", "--", ".", ".."], pd.NA
            )
            df['Data de Abertura'] = pd.to_datetime(df['Data de Abertura'], errors='coerce', dayfirst=True)
            df["mês"] = df['Data de Abertura'].dt.to_period('M')
        else:
            st.warning("Coluna 'Data de Abertura' não encontrada.")
            df["mês"] = None

        return df
    except FileNotFoundError:
        st.error("Arquivo 'ListaManifestacoes.csv' não encontrado.")
        return None

# --- Carregamento dos Dados ---
df_pesquisa = carregar_dados_pesquisa()
df_manifestacoes = carregar_dados_manifestacoes()

if df_pesquisa is None or df_manifestacoes is None:
    st.stop()

# --- Filtro de Tempo ---
st.sidebar.title("Filtro de Tempo")
usar_data_invalida = st.sidebar.checkbox("Incluir manifestações sem data?", value=False)

if "mês" in df_manifestacoes.columns and not df_manifestacoes["mês"].isnull().all():
    df_manifestacoes['mês_display'] = df_manifestacoes['mês'].dt.strftime('%B/%Y').str.capitalize()
    meses_disponiveis = sorted(df_manifestacoes["mês_display"].dropna().unique(), reverse=True)

    meses_selecionados_display = st.sidebar.multiselect(
        "Selecione o(s) mês(es):",
        options=meses_disponiveis,
        default=meses_disponiveis
    )

    meses_selecionados_periodo = pd.to_datetime(
        meses_selecionados_display, format="%B/%Y", errors="coerce"
    ).to_period('M')

    df_manifestacoes_filtrado = df_manifestacoes[
        (df_manifestacoes["mês"].isin(meses_selecionados_periodo)) |
        (usar_data_invalida & df_manifestacoes["mês"].isna())
    ]

    df_pesquisa_filtrado = df_pesquisa[
        df_pesquisa["mês"].isin(meses_selecionados_periodo)
    ]
else:
    st.sidebar.info("Filtro de tempo não disponível.")
    df_manifestacoes_filtrado = df_manifestacoes
    df_pesquisa_filtrado = df_pesquisa

# --- Layout Principal ---

st.title("📊 Dashboard Ouvidoria ANVISA")

tab1, tab2 = st.tabs(["Análise da Pesquisa de Satisfação", "Painel de Manifestações Gerais"])

# --- Aba 1 ---
with tab1:
    st.header("Análise da Pesquisa de Satisfação")
    if not df_pesquisa_filtrado.empty:
        st.metric("Total de Respostas no Período", f"{len(df_pesquisa_filtrado):,}".replace(",", "."))
        st.markdown("---")

        st.subheader("Classificação por Tipo de Manifestação")
        tipo = df_pesquisa_filtrado["Tipo de Manifestação"].value_counts().reset_index()
        tipo.columns = ['Tipo', 'Quantidade']
        fig_pie_tipo = px.pie(tipo, values='Quantidade', names='Tipo', title='Proporção por Tipo de Manifestação', hole=.3)
        st.plotly_chart(fig_pie_tipo, use_container_width=True)

        st.subheader("Avaliação do Atendimento")
        col_pesquisa1, col_pesquisa2 = st.columns(2)

        with col_pesquisa1:
            st.markdown("##### A sua demanda foi atendida?")
            avaliacao = df_pesquisa_filtrado["A sua demanda foi atendida?"].value_counts().reset_index()
            avaliacao.columns = ['Resposta', 'Quantidade']
            fig_avaliacao = px.bar(avaliacao, x='Quantidade', y='Resposta', color='Resposta', text='Quantidade')
            fig_avaliacao.update_layout(showlegend=False)
            st.plotly_chart(fig_avaliacao, use_container_width=True)

        with col_pesquisa2:
            st.markdown("##### Satisfação com o atendimento prestado")
            satisfacao = df_pesquisa_filtrado["Você está satisfeito(a) com o atendimento prestado?"].value_counts().reset_index()
            satisfacao.columns = ['Satisfação', 'Quantidade']
            fig_satisfacao = px.bar(satisfacao, x='Quantidade', y='Satisfação', color='Satisfação', text_auto=True)
            fig_satisfacao.update_layout(showlegend=False, yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_satisfacao, use_container_width=True)

        st.subheader("Distribuição de Respostas por Área")
        if "Área" in df_pesquisa_filtrado.columns:
            respostas_por_area = df_pesquisa_filtrado["Área"].value_counts().reset_index()
            respostas_por_area.columns = ['Área', 'Quantidade']
            fig_respostas_area = px.bar(respostas_por_area, x='Área', y='Quantidade', text_auto=True, color='Área')
            fig_respostas_area.update_layout(showlegend=False, xaxis_tickangle=-45)
            st.plotly_chart(fig_respostas_area, use_container_width=True)
        else:
            st.warning("Coluna 'Área' não encontrada na pesquisa.")
    else:
        st.info("Nenhum dado de pesquisa encontrado para o período selecionado.")

# --- Aba 2 ---
with tab2:
    st.header("Painel de Manifestações Gerais")
    st.metric("📌 Total de Manifestações no CSV", f"{len(df_manifestacoes):,}".replace(",", "."))

    if not df_manifestacoes_filtrado.empty:
        if 'NUP' in df_manifestacoes_filtrado.columns:
            total_manifestacoes_unicas = df_manifestacoes_filtrado['NUP'].nunique()
            st.metric("Total de Manifestações Únicas no Período", f"{total_manifestacoes_unicas:,}".replace(",", "."))
        else:
            st.metric("Total de Linhas no Período", f"{len(df_manifestacoes_filtrado):,}".replace(",", "."))

        st.markdown("---")

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Principais Temas das Manifestações")
            temas = df_manifestacoes_filtrado['Assunto'].value_counts().nlargest(10).reset_index()
            temas.columns = ['Tema', 'Quantidade']
            fig_temas = px.bar(temas, x='Quantidade', y='Tema', orientation='h', text='Quantidade')
            fig_temas.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_temas, use_container_width=True)

        with col2:
            st.subheader("Tipos de Manifestações Registradas")
            tipos_gerais = df_manifestacoes_filtrado['Tipo'].value_counts().reset_index()
            tipos_gerais.columns = ['Tipo', 'Quantidade']
            fig_tipos_gerais = px.bar(tipos_gerais, x='Quantidade', y='Tipo', orientation='h', text='Quantidade')
            fig_tipos_gerais.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_tipos_gerais, use_container_width=True)

        col3, col4 = st.columns(2)

        with col3:
            st.subheader("Distribuição de Manifestações por Área")
            
            # --- ATUALIZAÇÃO DO GRÁFICO DE ÁREA ---
            # 1. Contar as ocorrências de cada área
            area_counts = df_manifestacoes_filtrado["Área Responsável Resp. Concl."].value_counts()

            # 2. Definir o número de áreas principais a serem exibidas
            top_n = 15
            if len(area_counts) > top_n:
                # 3. Separar as top N áreas e as outras
                top_areas = area_counts.nlargest(top_n)
                outros_sum = area_counts.nsmallest(len(area_counts) - top_n).sum()
                
                
                area_plot_data = top_areas.reset_index()
            else:
                area_plot_data = area_counts.reset_index()

            area_plot_data.columns = ['Área', 'Quantidade']

            # 5. Criar o gráfico horizontal
            fig_area = px.bar(area_plot_data, 
                              x='Quantidade', 
                              y='Área', 
                              orientation='h', 
                              text='Quantidade',
                              title=f"Top {top_n} Áreas com Mais Manifestações")
            
            fig_area.update_layout(
                yaxis={'categoryorder':'total ascending'},
                xaxis_title="Nº de Manifestações",
                yaxis_title="Área Responsável",
                height=500 # Altura fixa para melhor visualização
            )
            st.plotly_chart(fig_area, use_container_width=True)

        with col4:
            st.subheader("Situação Atual das Manifestações")
            situacao = df_manifestacoes_filtrado['Situação'].value_counts().reset_index()
            situacao.columns = ['Situação', 'Quantidade']
            fig_situacao = px.bar(situacao, x='Quantidade', y='Situação', orientation='h', text='Quantidade')
            fig_situacao.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_situacao, use_container_width=True)
    else:
        st.info("Nenhuma manifestação encontrada para o período selecionado.")
