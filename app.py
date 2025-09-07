import streamlit as st
import time
from src.biblia_agent import BibliaAgent
from dotenv import load_dotenv

load_dotenv()

# Só existe a versão Ave Maria
versao_escolhida = "Ave Maria"

st.set_page_config(page_title="ScriptureMind", page_icon="📖")

# Estilo customizado
st.markdown(
    """
    <style>
        body {
            background-color: black;
        }
        .title {
            color: white;
            text-align: center;
            font-size: 36px;
            font-weight: bold;
        }
        .description {
            color: #d9d9d9;
            text-align: center;
            font-size: 18px;
            margin-bottom: 30px;
        }
        .chat-box {
            background-color: #1e1e1e;
            padding: 20px;
            border-radius: 12px;
            margin-bottom: 20px;
            color: #f5f5f5;
            font-size: 16px;
        }
        .user {
            color: #4da6ff;
            font-weight: bold;
        }
        .bot {
            color: #ffd700;
            font-weight: bold;
        }
        .loading {
            background-color: #333;
            color: #aaa;
            font-style: italic;
            padding: 15px;
            border-radius: 12px;
            margin-bottom: 20px;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# Título e descrição
st.markdown('<div class="title">ScriptureMind</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="description">O ScriptureMind é um sistema de estudo bíblico com busca inteligente de versículos e reflexões.<br><br><i>Autor: Vitor Eduardo de Lima Kenor</i><br><br><b>Versão utilizada: Bíblia Ave Maria</b></div>',
    unsafe_allow_html=True
)

# Criar ou atualizar agente conforme a versão
if "biblia_agent" not in st.session_state or st.session_state.get("versao_atual") != versao_escolhida:
    st.session_state.biblia_agent = BibliaAgent()
    st.session_state.versao_atual = versao_escolhida

# Inicializa o espaço da resposta
resposta_container = st.empty()

# Caixa de input estilo ChatGPT
user_input = st.chat_input("Digite sua pergunta...")

if user_input:
    # Balão de carregamento
    loading_placeholder = resposta_container.container()
    with loading_placeholder:
        msg = st.markdown('<div class="loading">⏳ O agente está buscando em suas ferramentas...</div>', unsafe_allow_html=True)

    # Simula animação com diferentes mensagens
    loading_msgs = [
        "🔍 Buscando versículos relacionados...",
        "📚 Consultando contexto bíblico...",
        "🧩 Montando a resposta final..."
    ]
    for step in loading_msgs:
        time.sleep(1.5)
        loading_placeholder.markdown(f'<div class="loading">{step}</div>', unsafe_allow_html=True)

    # Chama o agente
    response = st.session_state.biblia_agent.ask(user_input)

    # Substitui o balão pela resposta final
    with resposta_container.container():
        st.markdown(f'<div class="chat-box"><span class="user">Você:</span> {user_input}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="chat-box"><span class="bot">Bíblia (Ave Maria):</span> {response}</div>', unsafe_allow_html=True)

        # Download em TXT
        txt_content = f"# Pergunta\n{user_input}\n\n# Resposta\n{response}"
        st.download_button(
            label="Baixar Resposta",
            data=txt_content,
            file_name="resposta.txt",
            mime="text/plain"
        )
