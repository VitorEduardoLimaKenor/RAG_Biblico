from langchain_openai import OpenAI
from src.system_prompts import SYSTEM_INSTRUCTION_TEMPLATE, ANALISE_QUESTION
from src.chromadb_utils import ChromaDB
from langchain.agents import initialize_agent
from langchain.agents.agent_types import AgentType
import logging
from src.tools import (
    buscar_versiculos_semantica,
    buscar_dicionario_easton,
    buscar_na_biblia_json
)

# Logger de módulo
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

class BibliaAgent:
    def __init__(self, model_name: str = "gpt-4o-mini", temperature: float = 0.2):
        self.model_name = model_name
        self.temperature = temperature
        logger.info("Inicializando BibliaAgent | model=%s temperature=%.2f", self.model_name, self.temperature)
        try:
            self.db = ChromaDB()
            collections = self.db.ensure_collections()
            self.biblia = collections["biblia"]
            logger.info("Coleções ChromaDB carregadas com sucesso: biblia")
        except Exception as e:
            logger.exception("Falha ao inicializar ChromaDB/coleções: %s", e)
            raise

    def analisar_pergunta(self, question: str):
        """
        Analisa a pergunta do usuário para determinar se é relevante para o contexto bíblico.
        """
        logger.debug("Analisando pergunta recebida: %s", question)
        model = OpenAI(model=self.model_name, temperature=self.temperature)
        prompt = ANALISE_QUESTION.format(question=question)
        try:
            response = model.invoke(prompt)
            logger.info("Resultado da análise de escopo: %s", str(response))
            return response
        except Exception as e:
            logger.exception("Erro ao analisar pergunta: %s", e)
            raise

    def ask(self, question: str):
        """
        Faz uma pergunta ao agente bíblico utilizando o modelo LLM e ferramentas associadas.
        """
        logger.info("Iniciando processamento da pergunta do usuário")
        try:
            analise = self.analisar_pergunta(question)
        except Exception as e:
            logger.error("Erro na análise da pergunta, abortando: %s", e)
            return "Desculpe, ocorreu um erro ao processar sua pergunta."
        if "false" in analise.lower():
            logger.info("Pergunta fora de escopo bíblico. Encerrando com mensagem padrão.")
            return "Desculpe, não posso ajudar com essa pergunta. Por favor, faça uma pergunta relacionada a ensinamentos bíblicos."
        
        tools = [
            buscar_na_biblia_json,
            buscar_dicionario_easton,
            buscar_versiculos_semantica
        ]
        logger.debug("Configurando LLM e agente ReAct com ferramentas: %s", 
                     ", ".join([t.name if hasattr(t, 'name') else t.__name__ for t in tools]))

        llm = OpenAI(model=self.model_name, temperature=self.temperature, max_tokens=10000)
        
        # Usando ReAct Agent
        try:
            agent_executor = initialize_agent(
                tools=tools,
                llm=llm,
                agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
                verbose=True,
                handle_parsing_errors="Check your output and make sure it conforms to the expected format. Try again.",
                return_intermediate_steps=False
            )

            prompt = SYSTEM_INSTRUCTION_TEMPLATE.format(question=question)
            logger.debug("Invocando agente com prompt formatado")
            response = agent_executor.invoke(prompt)
            logger.info("Resposta gerada com sucesso pelo agente")
            return response['output']
        except Exception as e:
            logger.exception("Erro ao gerar resposta com o agente: %s", e)
            raise
