from langchain_groq import ChatGroq
from src.system_prompts import SYSTEM_INSTRUCTION_TEMPLATE, ANALISE_QUESTION
from src.chromadb_utils import ChromaDB
from langchain.agents import AgentExecutor, create_react_agent, initialize_agent
from langchain.agents.agent_types import AgentType
from langchain.prompts import ChatPromptTemplate
from src.tools import (
    buscar_versiculos_semantica,
    buscar_dicionario_easton,
    buscar_naves_topical,
    buscar_na_biblia_json
)

class BibliaAgent:
    def __init__(self, model_name: str = "llama-3.3-70b-versatile", temperature: float = 0.1):
        self.model_name = model_name
        self.temperature = temperature
        self.db = ChromaDB()
        collections = self.db.ensure_collections()
        self.biblia = collections["biblia"]
        self.easton = collections["dicionario"]
        self.naves = collections["naves"]

    def analisar_pergunta(self, question: str):
        """
        Analisa a pergunta do usuário para determinar se é relevante para o contexto bíblico.
        """
        model = ChatGroq(model=self.model_name, temperature=self.temperature)
        prompt = ANALISE_QUESTION.format(question=question)
        response = model.invoke(prompt)
        return response.content

    def ask(self, question: str):
        """
        Faz uma pergunta ao agente bíblico utilizando o modelo LLM e ferramentas associadas.
        """
        analise = self.analisar_pergunta(question)
        if "false" in analise.lower():
            return "Desculpe, não posso ajudar com essa pergunta. Por favor, faça uma pergunta relacionada a ensinamentos bíblicos."
        
        tools = [
            buscar_na_biblia_json,
            buscar_naves_topical,
            buscar_dicionario_easton,
            buscar_versiculos_semantica
        ]

        llm = ChatGroq(model=self.model_name, temperature=self.temperature)
        
        # Usando ReAct Agent
        agent_executor = initialize_agent(
            tools=tools,
            llm=llm,
            agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True,
            handle_parsing_errors="Check your output and make sure it conforms to the expected format. Try again.",
            return_intermediate_steps=False
            
        )

        prompt = SYSTEM_INSTRUCTION_TEMPLATE.format(question=question)
        response = agent_executor.invoke(prompt)
        return response['output']
