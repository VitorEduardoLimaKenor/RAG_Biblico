import streamlit as st
from agents.biblia_agent import Agent
from dotenv import load_dotenv

load_dotenv()

# Opções de versões da Bíblia
versoes = {
    "Ave Maria": "./settings/bibliaAveMaria_settings.py",
    "King James": "./settings/bibliaKingJames_settings.py"
}

models = {
    "gpt-oss-20b": "openai/gpt-oss-20b",
    "qwen3-32b": "qwen/qwen3-32b",
    "llama-3.3-70b-versatile": "llama-3.3-70b-versatile"
}

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
    </style>
    """,
    unsafe_allow_html=True
)

# Título e descrição
st.markdown('<div class="title">ScriptureMind</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="description">O ScriptureMind é um sistema de estudo bíblico com busca inteligente de versículos e reflexões.<br><br><i>Autor: Vitor Eduardo de Lima Kenor</i></div>',
    unsafe_allow_html=True
)

# Barra lateral para escolher versão
versao_escolhida = st.sidebar.selectbox("Escolha a versão da Bíblia:", list(versoes.keys()))
modelo_escolhido = st.sidebar.selectbox("Escolha o modelo de linguagem:", list(models.keys()))

# Criar ou atualizar agente conforme a versão
if "biblia_agent" not in st.session_state or st.session_state.get("versao_atual") != versao_escolhida:
    st.session_state.biblia_agent = Agent(settings_path=versoes[versao_escolhida], model=models[modelo_escolhido])
    st.session_state.versao_atual = versao_escolhida

# Inicializa o espaço da resposta
resposta_container = st.empty()

# Caixa de input estilo ChatGPT
user_input = st.chat_input("Digite sua pergunta...")

if user_input:
    response = st.session_state.biblia_agent.ask(user_input)

    # Exibe a resposta acima, estilo chat
    with resposta_container.container():
        st.markdown(f'<div class="chat-box"><span class="user">Você:</span> {user_input}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="chat-box"><span class="bot">Bíblia ({versao_escolhida}):</span> {response}</div>', unsafe_allow_html=True)

        # Download em TXT
        txt_content = f"# Pergunta\n{user_input}\n\n# Resposta\n{response}"
        st.download_button(
            label="Baixar Resposta",
            data=txt_content,
            file_name="resposta.txt",
            mime="text/plain"
        )