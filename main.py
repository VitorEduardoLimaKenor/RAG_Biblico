import streamlit as st
from agents.biblia_agent import Agent
from dotenv import load_dotenv

load_dotenv()

# Opções de versões da Bíblia
versoes = {
    "Ave Maria": "./settings/bibliaAveMaria_settings.py",
    "King James": "./settings/bibliaKingJames_settings.py"
}

st.set_page_config(page_title="Chat Bíblia", page_icon="📖")
st.title("📖 Chat Bíblia")

versao_escolhida = st.selectbox("Escolha a versão da Bíblia:", list(versoes.keys()))

if "biblia_agent" not in st.session_state or st.session_state.get("versao_atual") != versao_escolhida:
    st.session_state.biblia_agent = Agent(settings_path=versoes[versao_escolhida])
    st.session_state.versao_atual = versao_escolhida

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

user_input = st.text_input("Digite sua pergunta:", key="user_input")

if st.button("Enviar") and user_input.strip():
    response = st.session_state.biblia_agent.ask(user_input)
    st.session_state.chat_history.append((f"Você ({versao_escolhida})", user_input))
    st.session_state.chat_history.append(("Bíblia", response))

st.markdown("---")
for speaker, text in st.session_state.chat_history:
    st.markdown(f"**{speaker}:** {text}")