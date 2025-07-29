import streamlit as st
import pandas as pd
import plotly.express as px
import locale

# --- Configurações Iniciais ---

st.set_page_config(
    page_title="Dashboard Ouvidoria ANVISA",
    page_icon="📊",
    layout="wide"
)

# --- Funções de Carregamento de Dados ---

@st.cache_data
def carregar_dados_pesquisa():
    """
    Carrega e processa os dados da pesquisa de satisfação (pesquisa.csv).
    """
    try:
        df = pd.read_csv("pesquisa.csv", sep=";", encoding='utf-8')
        # Limpa a coluna de satisfação, se ela existir
        coluna_satisfacao = "Você está satisfeito(a) com o atendimento prestado?"
        if coluna_satisfacao in df.columns:
            df[coluna_satisfacao] = df[coluna_satisfacao].str.replace('?? ', '', regex=False).str.strip()
        
        # Processa a coluna de data para o filtro
        opcoes_coluna_data = ['Resposta à Pesquisa', 'Resposta à pesquisa']
        coluna_data_encontrada = None
        for coluna in opcoes_coluna_data:
            if coluna in df.columns:
                coluna_data_encontrada = coluna
                break
        if coluna_data_encontrada:
            df[coluna_data_encontrada] = pd.to_datetime(df[coluna_data_encontrada], errors='coerce')
            df.dropna(subset=[coluna_data_encontrada], inplace=True)
            # Usa a mesma coluna 'mês' para poder filtrar junto com o outro dataframe
            df["mês"] = df[coluna_data_encontrada].dt.to_period('M')
        return df
    except FileNotFoundError:
        st.error("Arquivo 'pesquisa.csv' não encontrado. Verifique se o arquivo está no seu repositório.")
        return None

@st.cache_data
def carregar_dados_manifestacoes():
    """
    Carrega e processa os dados gerais de manifestações (ListaManifestacoes.xlsx).
    """
    try:
        # ATENÇÃO: Verifique se o nome do arquivo é .xlsx ou .csv
        df = pd.read_excel("ListaManifestacoes.xlsx")
    except FileNotFoundError:
        st.error("Arquivo 'ListaManifestacoes.xlsx' não encontrado. Verifique se o arquivo está no seu repositório.")
        return None
    except Exception as e:
        st.error(f"Ocorreu um erro ao ler o arquivo Excel: {e}")
        return None

    # Processa a coluna de data para o filtro
    if 'Data de Abertura' in df.columns:
        df['Data de Abertura'] = pd.to_datetime(df['Data de Abertura'], errors='coerce')
        df.dropna(subset=['Data de Abertura'], inplace=True)
        df["mês"] = df['Data de Abertura'].dt.to_period('M')
    else:
        st.warning("Coluna 'Data de Abertura' não encontrada no arquivo de manifestações para o filtro de tempo.")
        df["mês"] = None
    
    return df

# --- Carregamento e Filtro Principal ---

df_pesquisa = carregar_dados_pesquisa()
df_manifestacoes = carregar_dados_manifestacoes()

if df_pesquisa is None or df_manifestacoes is None:
    st.stop()

st.sidebar.title("Filtro de Tempo")
st.sidebar.markdown("Use o filtro abaixo para analisar um período específico.")

# O filtro será baseado nos dados de manifestações
if "mês" in df_manifestacoes.columns and not df_manifestacoes["mês"].isnull().all():
    # Converte o período para uma string formatada para exibição
    df_manifestacoes['mês_display'] = df_manifestacoes['mês'].dt.strftime('%Y-%m')
    meses_disponiveis = sorted(list(df_manifestacoes["mês_display"].dropna().unique()), reverse=True)
    
    meses_selecionados_display = st.sidebar.multiselect(
        "Selecione o(s) mês(es):",
        options=meses_disponiveis,
        default=meses_disponiveis
    )
    # Converte a seleção de volta para o tipo período para filtragem
    meses_selecionados_periodo = pd.to_datetime(meses_selecionados_display).to_period('M')

    # Filtra os dois dataframes
    df_manifestacoes_filtrado = df_manifestacoes[df_manifestacoes["mês"].isin(meses_selecionados_periodo)]
    df_pesquisa_filtrado = df_pesquisa[df_pesquisa["mês"].isin(meses_selecionados_periodo)]
else:
    st.sidebar.info("Filtro de tempo não disponível.")
    df_manifestacoes_filtrado = df_manifestacoes
    df_pesquisa_filtrado = df_pesquisa

# --- Estrutura de Abas ---

st.title("📊 Dashboard Ouvidoria ANVISA")

tab1, tab2 = st.tabs(["Análise da Pesquisa de Satisfação", "Painel de Manifestações Gerais"])

# --- Aba 1: Análise da Pesquisa de Satisfação (usa df_pesquisa_filtrado) ---
with tab1:
    st.header("Análise da Pesquisa de Satisfação")
    # ... (código da aba 1 permanece o mesmo, mas usando df_pesquisa_filtrado) ...
    if not df_pesquisa_filtrado.empty:
        # ... (código dos gráficos da aba 1) ...
        st.metric("Total de Respostas no Período", f"{len(df_pesquisa_filtrado):,}".replace(",", "."))
    else:
        st.info("Nenhum dado de pesquisa encontrado para o período selecionado.")


# --- Aba 2: Painel de Manifestações Gerais (usa df_manifestacoes_filtrado) ---
with tab2:
    st.header("Painel de Manifestações Gerais")
    st.markdown("Esta aba apresenta uma visão geral de todas as manifestações recebidas.")

    if not df_manifestacoes_filtrado.empty:
        st.metric("Total de Manifestações no Período", f"{len(df_manifestacoes_filtrado):,}".replace(",", "."))
        st.markdown("---")

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Principais Temas das Manifestações")
            # Usa a coluna 'Assunto' do novo arquivo
            temas = df_manifestacoes_filtrado['Assunto'].value_counts().nlargest(10).reset_index()
            temas.columns = ['Tema', 'Quantidade']
            fig_temas = px.bar(temas, x='Quantidade', y='Tema', orientation='h', text='Quantidade')
            fig_temas.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_temas, use_container_width=True)

        with col2:
            st.subheader("Tipos de Manifestações Registradas")
            # Usa a coluna 'Tipo' do novo arquivo
            tipos_gerais = df_manifestacoes_filtrado['Tipo'].value_counts().reset_index()
            tipos_gerais.columns = ['Tipo', 'Quantidade']
            fig_tipos_gerais = px.bar(tipos_gerais, x='Quantidade', y='Tipo', orientation='h', text='Quantidade')
            fig_tipos_gerais.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_tipos_gerais, use_container_width=True)

        col3, col4 = st.columns(2)
        
        with col3:
            st.subheader("Distribuição de Manifestações por Área")
            # Usa a coluna 'Área Responsável' do novo arquivo
            area_resp = df_manifestacoes_filtrado["Área Responsável"].value_counts().reset_index()
            area_resp.columns = ['Área', 'Quantidade']
            fig_area_vertical = px.bar(area_resp, x='Área', y='Quantidade', color='Área', text_auto=True)
            fig_area_vertical.update_layout(showlegend=False, xaxis_tickangle=-45, xaxis={'categoryorder':'total descending'})
            st.plotly_chart(fig_area_vertical, use_container_width=True)
            
        with col4:
            st.subheader("Situação Atual das Manifestações")
            # Usa a coluna 'Situação' do novo arquivo
            situacao = df_manifestacoes_filtrado['Situação'].value_counts().reset_index()
            situacao.columns = ['Situação', 'Quantidade']
            fig_situacao = px.bar(situacao, x='Quantidade', y='Situação', orientation='h', text='Quantidade')
            fig_situacao.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_situacao, use_container_width=True)

    else:
        st.info("Nenhuma manifestação encontrada para o período selecionado.")
