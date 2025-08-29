from langchain.prompts import PromptTemplate

# ------------------ llm settings ------------------ #

TEMPERATURE=1

# ------------------ RAG settings ------------------ #

# Caminho para o arquivo da Bíblia
BIBLIA_PATH="./data/bibliaKingJames.json"

# Caminho para o banco de dados Chroma
CHROMA_PATH="./data/chroma_db"

# Nome da coleção no banco de dados Chroma
COLLECTION_NAME="bibliaKingJames"

# Número de versículos a serem retornados na busca
NUM_VERSICULOS=5

# ------------------ Prompt settings ------------------ #

# Instrução específica
SYSTEM_INSTRUCTION_TEMPLATE = PromptTemplate(
    input_variables=["versiculos"],
    template="""
    ### Sua tarefa
    Você é um assistente bíblico. 
    Você deve responder à pergunta do usuário usando apenas os versículos fornecidos como contexto.

    ---

    ### Versículos encontrados:
    {versiculos}

    ---

    ### Instruções:
    - Traga os versículos relevantes dentro da resposta, citando livro, capítulo e versículo.  
    - Explique em linguagem clara e acolhedora o que eles ensinam sobre a pergunta.  
    - Mostre os aprendizados e aplicações práticas que podem ser tirados.  
    - Não invente versículos que não estão no contexto fornecido.  
    - Se não houver versículos suficientes, apenas explique com base no que foi encontrado.
    """
)