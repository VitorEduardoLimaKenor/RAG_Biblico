# ------------------ llm settings ------------------ #

TEMPERATURE=1

# ------------------ RAG settings ------------------ #

# Caminho para o arquivo da Bíblia
BIBLIA_PATH="./src/data/biblias/bibliaAveMaria.json"

# Caminho para o banco de dados Chroma
CHROMA_PATH="./src/data/chroma_db"

# Nome da coleção no banco de dados Chroma
COLLECTION_NAME="bibliaAveMaria"

# Número de versículos a serem retornados na busca
NUM_VERSICULOS=3

# ------------------ Prompt settings ------------------ #

# Instrução específica
SYSTEM_INSTRUCTION_TEMPLATE = """
### Sua tarefa
    Você é um assistente bíblico. Use **exatamente** os nomes das ferramentas abaixo, sem adicionar sufixos, prefixos ou modificações:

    Tool(name="Busca_Versiculos")
    Tool(name="Busca_Tematica_Naves")
    Tool(name="Busca_Historica_Easton")
    Tool(name="Busca_Estrutural_Biblia_JSON")

    Não invente nomes de ferramentas. Use apenas os nomes acima.

### Exemplos simples de uso das ferramentas

- Busca_Versiculos("fé")
- Busca_Tematica_Naves("amor")
- Busca_Historica_Easton("José")
- Busca_Estrutural_Biblia_JSON("João 3")
"""
