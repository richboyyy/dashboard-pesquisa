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
# Isso pode ser necessário dependendo do ambiente onde o app está rodando.
try:
    locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
except locale.Error:
    st.warning("Locale 'pt_BR.UTF-8' não encontrado. Os nomes dos meses podem aparecer em inglês.")

# --- Carregamento e Pré-processamento dos Dados ---

# Usamos um bloco try-except para lidar com o caso de o arquivo não ser encontrado.
@st.cache_data
def carregar_dados():
    try:
        # Carrega os dados do arquivo CSV
        df = pd.read_csv("pesquisa.csv", sep=";", encoding="latin1")
        # Converte a coluna de data, tratando erros ao converter para NaT (Not a Time)
        df["Resposta à Pesquisa"] = pd.to_datetime(df["Resposta à Pesquisa"], errors="coerce")
        # Remove linhas onde a data não pôde ser convertida
        df.dropna(subset=["Resposta à Pesquisa"], inplace=True)
        # Extrai o nome do mês em minúsculas
        df["mês"] = df["Resposta à Pesquisa"].dt.month_name().str.lower()
        return df
    except FileNotFoundError:
        st.error("Erro: O arquivo 'pesquisa.csv' não foi encontrado. Por favor, certifique-se de que o arquivo está na mesma pasta que o seu script `app.py`.")
        return None

df = carregar_dados()

if df is None:
    st.stop() # Interrompe a execução do script se o arquivo não for encontrado.


# --- Barra Lateral (Sidebar) com Filtros ---

st.sidebar.title("🗓️ Filtro de Tempo")
st.sidebar.markdown("Use o filtro abaixo para analisar um período específico.")

# Obtém a lista de meses únicos e a ordena
# Usamos list() para garantir que a ordem seja preservada após o sorted()
meses_disponiveis = sorted(list(df["mês"].dropna().unique()))

meses_selecionados = st.sidebar.multiselect(
    "Selecione o(s) mês(es):",
    options=meses_disponiveis,
    default=meses_disponiveis # Por padrão, todos os meses vêm selecionados
)

# Filtra o DataFrame com base na seleção.
if meses_selecionados:
    df_filtrado = df[df["mês"].isin(meses_selecionados)]
else:
    # Se nenhum mês for selecionado, o ideal é mostrar uma mensagem em vez de um dashboard vazio
    st.warning("Por favor, selecione pelo menos um mês na barra lateral para visualizar os dados.")
    df_filtrado = pd.DataFrame() # Cria um DataFrame vazio para evitar erros nos gráficos

# --- Página Principal ---

st.title("📊 Dashboard de Análise de Manifestações da ANVISA")
st.markdown("Este painel apresenta uma análise das respostas da pesquisa de satisfação.")

# Verifica se o dataframe filtrado não está vazio antes de tentar renderizar o resto da página
if not df_filtrado.empty:
    # --- Métricas Principais ---
    col1, col2 = st.columns(2)
    col1.metric("Total de Respostas no Período", len(df_filtrado))
    # Exemplo de outra métrica que você poderia adicionar
    col2.metric("Período Analisado", f"{len(meses_selecionados)} mese(s)")

    st.markdown("---") # Linha divisória

    # --- Gráficos ---

    # Gráfico 1 - Área Responsável
    st.subheader("Distribuição de Manifestações por Área")
    # ATUALIZAÇÃO: Usando a coluna "Área"
    area_resp = df_filtrado["Área"].value_counts().reset_index()
    area_resp.columns = ['Área', 'Quantidade']
    fig1 = px.bar(area_resp, x='Quantidade', y='Área', orientation='h',
                  color='Área',
                  labels={'Quantidade': 'Nº de Manifestações', 'Área': 'Área Responsável'},
                  text='Quantidade')
    fig1.update_layout(showlegend=False) # Esconde a legenda para um visual mais limpo
    st.plotly_chart(fig1, use_container_width=True)

    # Gráfico 2 - Tipo de Manifestação
    st.subheader("Classificação por Tipo de Manifestação")
    # ATUALIZAÇÃO: Usando a coluna "Tipo de Manifestação"
    tipo = df_filtrado["Tipo de Manifestação"].value_counts().reset_index()
    tipo.columns = ['Tipo', 'Quantidade']
    fig2 = px.pie(tipo, values='Quantidade', names='Tipo',
                  title='Proporção por Tipo de Manifestação',
                  hole=.3) # Gráfico de rosca para variar
    st.plotly_chart(fig2, use_container_width=True)


    # Gráfico 3 - Atendimento à Demanda e Satisfação com Atendimento
    st.subheader("Avaliação do Atendimento")
    col3, col4 = st.columns(2)

    with col3:
        # ATUALIZAÇÃO: Usando a coluna "A sua demanda foi atendida?"
        st.markdown("##### A sua demanda foi atendida?")
        avaliacao = df_filtrado["A sua demanda foi atendida?"].value_counts().reset_index()
        avaliacao.columns = ['Resposta', 'Quantidade']
        fig3 = px.bar(avaliacao, x='Quantidade', y='Resposta', color='Resposta',
                      labels={'Quantidade': 'Contagem', 'Resposta': 'Resposta do Usuário'},
                      text='Quantidade')
        fig3.update_layout(showlegend=False)
        st.plotly_chart(fig3, use_container_width=True)

    with col4:
        # ATUALIZAÇÃO: Usando a coluna "Você está satisfeito(a) com o atendimento prestado?"
        st.markdown("##### Satisfação com o atendimento prestado")
        satisfacao = df_filtrado["Você está satisfeito(a) com o atendimento prestado?"].value_counts().reset_index()
        satisfacao.columns = ['Satisfação', 'Quantidade']
        fig4 = px.bar(satisfacao, x='Quantidade', y='Satisfação', color='Satisfação',
                      labels={'Quantidade': 'Contagem', 'Satisfação': 'Nível de Satisfação'},
                      text_auto=True)
        fig4.update_layout(showlegend=False)
        st.plotly_chart(fig4, use_container_width=True)

else:
    # Se o dataframe estiver vazio (nenhum mês selecionado), a mensagem de aviso já foi exibida.
    st.info("Selecione os meses na barra à esquerda para começar a análise.")
