import streamlit as st
import pandas as pd
import plotly.express as px
import locale

# --- Configurações Iniciais ---

# Define a configuração da página. Isso deve ser o primeiro comando do Streamlit.
st.set_page_config(
    page_title="Dashboard de Manifestações ANVISA",
    page_icon="📊",
    layout="wide"
)

# Define o locale para português do Brasil para garantir que os nomes dos meses fiquem corretos.
try:
    locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
except locale.Error:
    st.warning("Locale 'pt_BR.UTF-8' não encontrado. Os nomes dos meses podem aparecer em inglês.")

# --- Carregamento e Pré-processamento dos Dados ---

@st.cache_data
def carregar_dados():
    """
    Carrega os dados do CSV e os pré-processa.
    Esta função foi atualizada para ser mais robusta contra erros de nome de coluna.
    """
    try:
        # ATUALIZAÇÃO FINAL: Alterado o encoding para "cp1252", que é comum para arquivos Windows em português.
        df = pd.read_csv("pesquisa.csv", sep=";", encoding="cp1252")
    except FileNotFoundError:
        st.error("Erro: O arquivo 'pesquisa.csv' não foi encontrado. Por favor, certifique-se de que o arquivo está no seu repositório GitHub junto com o script do app.")
        return None
    except Exception as e:
        st.error(f"Ocorreu um erro ao ler o arquivo CSV. Verifique o formato e a codificação do arquivo. Erro: {e}")
        return None


    # ATUALIZAÇÃO: Lógica para encontrar a coluna de data correta
    # Lista de possíveis nomes para a coluna de data que queremos processar.
    opcoes_coluna_data = ['Resposta à Pesquisa', 'Resposta à pesquisa']
    coluna_data_encontrada = None

    # Procura por uma das opções de coluna no DataFrame carregado.
    for coluna in opcoes_coluna_data:
        if coluna in df.columns:
            coluna_data_encontrada = coluna
            break # Para o loop assim que encontrar a primeira correspondência

    # Se, após o loop, nenhuma coluna de data for encontrada, exibe um erro claro e a lista de colunas disponíveis.
    if coluna_data_encontrada is None:
        st.error(
            "Erro Crítico: Não foi possível encontrar uma coluna de data ('Resposta à Pesquisa' ou 'Resposta à pesquisa') no arquivo CSV."
        )
        st.warning("Verifique se o nome da coluna no seu arquivo `pesquisa.csv` corresponde a uma das opções acima.")
        st.info("As colunas que foram encontradas no arquivo são:")
        st.code(df.columns.tolist()) # Mostra as colunas exatas para depuração
        return None

    # Se a coluna foi encontrada, prossegue com o processamento
    try:
        df[coluna_data_encontrada] = pd.to_datetime(df[coluna_data_encontrada], errors='coerce')
        df.dropna(subset=[coluna_data_encontrada], inplace=True)
        df["mês"] = df[coluna_data_encontrada].dt.month_name().str.lower()
        return df
    except Exception as e:
        st.error(f"Ocorreu um erro ao processar a coluna de data '{coluna_data_encontrada}': {e}")
        return None


df = carregar_dados()

if df is None:
    st.stop() # Interrompe a execução do script se os dados não puderem ser carregados.


# --- Barra Lateral (Sidebar) com Filtros ---

st.sidebar.title("🗓️ Filtro de Tempo")
st.sidebar.markdown("Use o filtro abaixo para analisar um período específico.")

meses_disponiveis = sorted(list(df["mês"].dropna().unique()))

meses_selecionados = st.sidebar.multiselect(
    "Selecione o(s) mês(es):",
    options=meses_disponiveis,
    default=meses_disponiveis
)

# Filtra o DataFrame com base na seleção.
if meses_selecionados:
    df_filtrado = df[df["mês"].isin(meses_selecionados)]
else:
    st.warning("Por favor, selecione pelo menos um mês na barra lateral para visualizar os dados.")
    df_filtrado = pd.DataFrame()

# --- Página Principal ---

st.title("📊 Dashboard de Análise de Manifestações da ANVISA")
st.markdown("Este painel apresenta uma análise das respostas da pesquisa de satisfação.")

if not df_filtrado.empty:
    # --- Métricas Principais ---
    col1, col2 = st.columns(2)
    col1.metric("Total de Respostas no Período", len(df_filtrado))
    col2.metric("Período Analisado", f"{len(meses_selecionados)} mese(s)")

    st.markdown("---")

    # --- Gráficos ---

    # Gráfico 1 - Área Responsável
    st.subheader("Distribuição de Manifestações por Área")
    area_resp = df_filtrado["Área"].value_counts().reset_index()
    area_resp.columns = ['Área', 'Quantidade']
    fig1 = px.bar(area_resp, x='Quantidade', y='Área', orientation='h',
                  color='Área',
                  labels={'Quantidade': 'Nº de Manifestações', 'Área': 'Área Responsável'},
                  text='Quantidade')
    fig1.update_layout(showlegend=False)
    st.plotly_chart(fig1, use_container_width=True)

    # Gráfico 2 - Tipo de Manifestação
    st.subheader("Classificação por Tipo de Manifestação")
    tipo = df_filtrado["Tipo de Manifestação"].value_counts().reset_index()
    tipo.columns = ['Tipo', 'Quantidade']
    fig2 = px.pie(tipo, values='Quantidade', names='Tipo',
                  title='Proporção por Tipo de Manifestação',
                  hole=.3)
    st.plotly_chart(fig2, use_container_width=True)


    # Gráfico 3 - Avaliação do Atendimento
    st.subheader("Avaliação do Atendimento")
    col3, col4 = st.columns(2)

    with col3:
        st.markdown("##### A sua demanda foi atendida?")
        avaliacao = df_filtrado["A sua demanda foi atendida?"].value_counts().reset_index()
        avaliacao.columns = ['Resposta', 'Quantidade']
        fig3 = px.bar(avaliacao, x='Quantidade', y='Resposta', color='Resposta',
                      labels={'Quantidade': 'Contagem', 'Resposta': 'Resposta do Usuário'},
                      text='Quantidade')
        fig3.update_layout(showlegend=False)
        st.plotly_chart(fig3, use_container_width=True)

    with col4:
        st.markdown("##### Satisfação com o atendimento prestado")
        satisfacao = df_filtrado["Você está satisfeito(a) com o atendimento prestado?"].value_counts().reset_index()
        satisfacao.columns = ['Satisfação', 'Quantidade']
        fig4 = px.bar(satisfacao, x='Quantidade', y='Satisfação', color='Satisfação',
                      labels={'Quantidade': 'Contagem', 'Satisfação': 'Nível de Satisfação'},
                      text_auto=True)
        fig4.update_layout(showlegend=False)
        st.plotly_chart(fig4, use_container_width=True)

else:
    st.info("Selecione os meses na barra à esquerda para começar a análise.")
