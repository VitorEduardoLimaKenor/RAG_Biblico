import streamlit as st
from dotenv import load_dotenv
import logging
import os

# Importa as ferramentas para apresentar 
from src.tools import (
    buscar_na_biblia_json,
    buscar_dicionario_easton,
    buscar_versiculos_semantica
)

# Importa o agente do projeto
from src.biblia_agent import BibliaAgent, APIRateLimitError

# Configuração de página (precisa vir antes de qualquer output)
st.set_page_config(
    page_title="Projeto RAG Bíblico",
    page_icon="✝️",
    layout="wide"
)

# CSS para deixar o layout mais espaçoso e menos centralizado
st.markdown(
    """
    <style>
    .block-container {max-width: 1400px; padding-top: 2rem; padding-bottom: 3rem;}
    .stTabs [data-baseweb="tab-list"] {gap: 12px;}
    .stTabs [data-baseweb="tab"] {padding: 10px 16px;}
    </style>
    """,
    unsafe_allow_html=True,
)

# ------------------------- Cabeçalho ------------------------- #
st.title("✝️ Projeto RAG Bíblico ✝️")
st.caption("Ferramenta interativa para estudo e pesquisa bíblica, combinando inteligência artificial com dados históricos e textuais da Bíblia.")
st.caption("Desenvolvido por: Vitor Eduardo de Lima Kenor")

# ------------------------- Configuração básica ------------------------- #

load_dotenv()

# Configuração centralizada de logging
level_name = os.getenv("LOG_LEVEL", "INFO").upper()
level = getattr(logging, level_name, logging.INFO)

# Garante que exista um handler de console para o root logger (sem duplicar)
root_logger = logging.getLogger()
if not root_logger.handlers:
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%H:%M:%S"
    ))
    root_logger.addHandler(console_handler)

# Ajusta o nível do root logger conforme variável de ambiente
root_logger.setLevel(level)

# Captura warnings do módulo warnings no logging
logging.captureWarnings(True)

# Handler de logging para exibir logs em tempo real no Streamlit durante a inicialização
class StreamlitLogHandler(logging.Handler):
    def __init__(self, placeholder: "st.delta_generator.DeltaGenerator"):
        super().__init__()
        self.placeholder = placeholder
        self.logs = []
        self.setFormatter(logging.Formatter(
            fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            datefmt="%H:%M:%S"
        ))

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)
            self.logs.append(msg)
            # Mantém apenas as últimas 300 linhas para evitar crescer indefinidamente
            if len(self.logs) > 300:
                self.logs = self.logs[-300:]
            self.placeholder.code("\n".join(self.logs), language="text")
        except Exception:
            # Não deixa o logging quebrar o app
            pass

# Garante uma única instância do agente por sessão do usuário e mostra tela de carregamento com logs
if "agent" not in st.session_state:
    loading_container = st.container()
    with loading_container:
        log_area = st.empty()
        handler = StreamlitLogHandler(log_area)
        root_logger.addHandler(handler)

        try:
            with st.spinner("Carregando recursos (ChromaDB, embeddings, coleções)..."):
                # A criação do agente deverá emitir logs que aparecerão acima em tempo real
                st.session_state.agent = BibliaAgent()
        except Exception as e:
            st.error(f"Falha na inicialização: {e}")
        finally:
            # Remove o handler para evitar logs duplicados após a inicialização
            root_logger.removeHandler(handler)
            # Limpa a área de logs e o container de carregamento
            try:
                log_area.empty()
            except Exception:
                pass
            loading_container.empty()

agent = st.session_state.get("agent")
if agent is None:
    st.stop()

# ------------------------- Abas ------------------------- #
tabs = st.tabs([
    "Agente Bíblico",
    "Leitura por capítulo",
    "Tool de busca no Dicionário Easton",
    "Tool de busca semântica na Bíblia"
])

# ------------------------- Aba 1: Pergunte ao Agente ------------------------- #
with tabs[0]:
    st.subheader("Pergunte algo relacionado à Bíblia")
    question = st.text_area("Sua pergunta", placeholder="Ex.: O que a Bíblia ensina sobre perdão?", height=120)
    ask_clicked = st.button("Perguntar", type="primary", use_container_width=True)

    if ask_clicked:
        with st.spinner("Consultando o agente..."):
            try:
                answer = agent.ask(question)
                st.markdown("**Resposta:**")
                st.write(answer)
            except APIRateLimitError as e:
                # Mensagem específica para rate limit com indicação de quando tentar novamente
                if getattr(e, "retry_text", None):
                    st.error(f"Limite de chamadas da API atingido. Tente novamente em {e.retry_text}.")
                else:
                    st.error("Limite de chamadas da API atingido. Tente novamente em breve.")
            except Exception as e:
                st.error(f"Erro ao consultar o agente: {e}")

# ------------------------- Aba 2: Leitura por Capítulo ------------------------- #
with tabs[1]:
    st.subheader("Leitura direta por capítulo")
    livro = st.text_input("Livro (nome ou abreviação)", placeholder="Ex.: Gênesis")
    cap = st.number_input("Capítulo", min_value=1, value=1, step=1)
    ler_clicked = st.button("Ler capítulo", use_container_width=True)

    if ler_clicked:
        with st.spinner("Carregando capítulo..."):
            try:
                result = buscar_na_biblia_json(f"{livro}:{cap}")
                if not result:
                    st.warning("Não encontrado. Verifique o nome do livro e o capítulo.")
                else:
                    st.markdown(f"### {result['referencia']}")
                    for v in result["versiculos"]:
                        st.markdown(f"**{v['versiculo']}**. {v['texto']}")
            except Exception as e:
                st.error(f"Erro ao ler capítulo: {e}")

# ------------------------- Aba 3: Dicionário Easton ------------------------- #
with tabs[2]:
    st.subheader("Consulta ao Dicionário Bíblico de Easton")
    easton_query = st.text_input("Termo para buscar", placeholder="Ex.: Jesus, fariseus, Jerusalém")
    easton_clicked = st.button("Buscar no Easton", use_container_width=True)

    if easton_clicked:
        with st.spinner("Buscando no Easton..."):
            try:
                res = buscar_dicionario_easton(easton_query)
                st.code(res)
            except Exception as e:
                st.error(f"Erro ao buscar no Easton: {e}")

# ------------------------- Aba 4: Busca Semântica ------------------------- #
with tabs[3]:
    st.subheader("Tool de Busca Semântica")
    semantica_query = st.text_input("Termo para buscar", placeholder="Ex.: perdão")
    semantica_clicked = st.button("Buscar semântica", use_container_width=True)

    if semantica_clicked:
        with st.spinner("Buscando semântica..."):
            try:
                res = buscar_versiculos_semantica(semantica_query)
                st.code(res)
            except Exception as e:
                st.error(f"Erro ao buscar semântica: {e}")

# ------------------------- Rodapé ------------------------- #
st.divider()
st.caption("Modelo de linguagem: llama-3.3-70b-versatile")