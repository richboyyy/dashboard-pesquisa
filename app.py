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

# Tenta configurar o locale para português. Isso garante que os nomes dos meses
# na interface (ex: "Setembro") sejam exibidos corretamente.
try:
    locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
except locale.Error:
    st.warning("Locale 'pt_BR.UTF-8' não encontrado. Os nomes dos meses podem aparecer em inglês.")

# --- Funções de Carregamento de Dados ---

@st.cache_data
def carregar_dados_pesquisa():
    """
    Carrega e processa os dados da pesquisa de satisfação (pesquisa.csv).
    """
    try:
        # Usando utf-8 que é mais padrão e robusto para caracteres especiais.
        df = pd.read_csv("pesquisa.csv", sep=";")
        df.columns = df.columns.str.strip()

        coluna_satisfacao = "Você está satisfeito(a) com o atendimento prestado?"
        if coluna_satisfacao in df.columns:
            df[coluna_satisfacao] = df[coluna_satisfacao].str.replace('?? ', '', regex=False).str.strip()

        opcoes_coluna_data = ['Resposta à Pesquisa', 'Resposta à pesquisa']
        coluna_data_encontrada = None
        for coluna in opcoes_coluna_data:
            if coluna in df.columns:
                coluna_data_encontrada = coluna
                break
        
        # CORREÇÃO: Garante que a coluna 'mês' seja sempre criada.
        if coluna_data_encontrada:
            df[coluna_data_encontrada] = pd.to_datetime(df[coluna_data_encontrada], errors='coerce', dayfirst=True)
            df["mês"] = df[coluna_data_encontrada].dt.to_period('M')
        else:
            # Se não encontrar coluna de data, cria a coluna 'mês' com valores nulos.
            st.warning("Nenhuma coluna de data encontrada no arquivo 'pesquisa.csv'. O filtro de tempo não será aplicado a este dataset.")
            df["mês"] = None
        
        return df
    except FileNotFoundError:
        st.error("Arquivo 'pesquisa.csv' não encontrado.")
        return None
    except Exception as e:
        st.error(f"Erro ao carregar 'pesquisa.csv': {e}")
        return None

@st.cache_data
def carregar_dados_manifestacoes():
    """
    Carrega e processa os dados gerais de manifestações (ListaManifestacoes.csv).
    """
    try:
        df = pd.read_csv("ListaManifestacaoAtualizadaa.csv", sep=";", encoding= 'utf-8')

# Normaliza colunas
        df.columns = (
        df.columns
        .str.strip()       # remove espaços antes/depois
        .str.replace("﻿", "", regex=False)  # remove caracteres ocultos (BOM)
        .str.replace("\uFEFF", "", regex=False)  # remove BOM explícito
)

        # Renomeia a coluna problemática, se existir, para um nome padrão.
        for col in df.columns:
            if "Área Responsável" in col:
                df.rename(columns={col: "Área Responsável"}, inplace=True)
                break

        if 'Data de Abertura' in df.columns:
            df['Data de Abertura'] = pd.to_datetime(df['Data de Abertura'], errors='coerce', dayfirst=True)
            df["mês"] = df['Data de Abertura'].dt.to_period('M')
        else:
            st.warning("Coluna 'Data de Abertura' não encontrada.")
            df["mês"] = None

        return df
    except FileNotFoundError:
        st.error("Arquivo 'ListaManifestacoes.csv' não encontrado.")
        return None
    except Exception as e:
        st.error(f"Erro ao carregar 'ListaManifestacoes.csv': {e}")
        return None

# --- Carregamento dos Dados ---
df_pesquisa = carregar_dados_pesquisa()
df_manifestacoes = carregar_dados_manifestacoes()

if df_pesquisa is None or df_manifestacoes is None:
    st.stop()

# --- Filtro de Tempo (SEÇÃO CORRIGIDA) ---
st.sidebar.title("Filtro de Tempo")
usar_data_invalida = st.sidebar.checkbox("Incluir manifestações sem data?", value=False)

# Verifica se a coluna de mês existe e não está completamente vazia
if "mês" in df_manifestacoes.columns and not df_manifestacoes["mês"].isnull().all():
    
    # 1. Pega os períodos únicos e válidos e os ordena
    meses_periodo_unicos = sorted(df_manifestacoes["mês"].dropna().unique(), reverse=True)
    
    # 2. Cria um dicionário para mapear o texto de exibição (ex: "Setembro/2025") de volta para o objeto de período original
    #    Isso evita a necessidade de converter strings de volta para datas mais tarde.
    mapa_mes_display_para_periodo = {
        periodo.strftime('%B/%Y').capitalize(): periodo 
        for periodo in meses_periodo_unicos
    }
    
    # 3. Pega as chaves do dicionário (os textos) para usar como opções no multiselect
    opcoes_meses_display = list(mapa_mes_display_para_periodo.keys())

    # 4. Exibe o multiselect para o usuário
    meses_selecionados_display = st.sidebar.multiselect(
        "Selecione o(s) mês(es):",
        options=opcoes_meses_display,
        default=opcoes_meses_display  # Por padrão, todos vêm selecionados
    )

    # 5. Usa o dicionário para converter os textos selecionados de volta para os objetos de período
    meses_selecionados_periodo = [
        mapa_mes_display_para_periodo[display] for display in meses_selecionados_display
    ]

    # 6. Filtra os DataFrames usando a lista de períodos
    df_manifestacoes_filtrado = df_manifestacoes[
        (df_manifestacoes["mês"].isin(meses_selecionados_periodo)) |
        (usar_data_invalida & df_manifestacoes["mês"].isna())
    ]

    # Filtra o dataframe de pesquisa apenas se ele tiver a coluna 'mês' válida
    if "mês" in df_pesquisa.columns and not df_pesquisa["mês"].isnull().all():
        df_pesquisa_filtrado = df_pesquisa[
            df_pesquisa["mês"].isin(meses_selecionados_periodo)
        ]
    else:
        # Se não houver mês, não filtra
        df_pesquisa_filtrado = df_pesquisa
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
    st.metric("📩 Total de Manifestações", f"{len(df_manifestacoes):,}".replace(",", "."))

    if not df_manifestacoes_filtrado.empty:
        
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
            if "Área Responsável" in df_manifestacoes_filtrado.columns:
                area_counts = df_manifestacoes_filtrado["Área Responsável"].value_counts().reset_index()
                area_counts.columns = ['Área Responsável', 'Total de Manifestações']

                total_row = pd.DataFrame({
                    'Área Responsável': ['Total'],
                    'Total de Manifestações': [area_counts['Total de Manifestações'].sum()]
                })
                
                area_display_table = pd.concat([area_counts, total_row], ignore_index=True)
                st.dataframe(area_display_table, use_container_width=True, hide_index=True)
            else:
                st.error("Coluna 'Área Responsável' não encontrada.")

        with col4:
            st.subheader("Situação Atual das Manifestações")
            situacao = df_manifestacoes_filtrado['Situação'].value_counts().reset_index()
            situacao.columns = ['Situação', 'Quantidade']
            fig_situacao = px.bar(situacao, x='Quantidade', y='Situação', orientation='h', text='Quantidade')
            fig_situacao.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_situacao, use_container_width=True)
    else:
        st.info("Nenhuma manifestação encontrada para o período selecionado.")