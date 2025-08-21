from langchain_groq import ChatGroq

# Função para construir o LLM
def build_llm(model: str, temperature: float):
    """
    Cria um modelo de linguagem com parâmetros específicos.
    """
    llm = ChatGroq(
        model=model,
        temperature=temperature,
    )
    return llm

