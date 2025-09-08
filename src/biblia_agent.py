from langchain_groq import ChatGroq
from src.system_prompts import SYSTEM_INSTRUCTION_TEMPLATE, ANALISE_QUESTION
from src.chromadb_utils import ChromaDB
from langchain.agents import initialize_agent
from langchain.agents.agent_types import AgentType
import logging
import re
from typing import Optional, Tuple
from groq import RateLimitError
from src.tools import (
    buscar_versiculos_semantica,
    buscar_dicionario_easton,
    buscar_na_biblia_json
)

# Logger de módulo
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

class APIRateLimitError(Exception):
    """
    Erro customizado para limites de requisição da API (HTTP 429).
    Inclui o texto retornado e, quando possível, os segundos sugeridos para aguardar.
    """
    def __init__(self, message: str, retry_seconds: Optional[int] = None, retry_text: Optional[str] = None):
        super().__init__(message)
        self.retry_seconds = retry_seconds
        self.retry_text = retry_text or ""

def _parse_retry_from_message(msg: str) -> Tuple[Optional[int], Optional[str]]:
    """Tenta extrair o tempo de espera sugerido da mensagem da Groq.
    Exemplos de trechos: "Please try again in 2m23.206s." ou "Please try again in 45.000s."
    Retorna (retry_seconds, retry_text)
    """
    try:
        # Formato com minutos e segundos: 2m23.206s
        m = re.search(r"Please try again in\s+(?:(\d+)m)?(\d+(?:\.\d+)?)s", msg)
        if m:
            minutes = m.group(1)
            seconds = float(m.group(2))
            total_seconds = int(seconds)
            if minutes is not None:
                total_seconds += int(minutes) * 60
            # Texto amigável aproximado
            if total_seconds >= 60:
                mins = total_seconds // 60
                secs = total_seconds % 60
                text = f"~{mins}m{secs}s"
            else:
                text = f"~{total_seconds}s"
            return total_seconds, text
    except Exception:
        pass
    return None, None

class BibliaAgent:
    def __init__(self, model_name: str = "llama-3.3-70b-versatile", temperature: float = 0.2):
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
        model = ChatGroq(model=self.model_name, temperature=self.temperature)
        prompt = ANALISE_QUESTION.format(question=question)
        try:
            response = model.invoke(prompt)
            logger.info("Resultado da análise de escopo: %s", str(response.content))
            return response.content
        except RateLimitError as e:
            # Trata especificamente rate limit da Groq e reenvia como erro customizado
            msg = str(getattr(e, "body", getattr(e, "message", str(e))))
            retry_seconds, retry_text = _parse_retry_from_message(msg)
            logger.warning("Rate limit atingido em analisar_pergunta. retry=%s", retry_text or retry_seconds)
            raise APIRateLimitError("Limite de chamadas da API atingido.", retry_seconds=retry_seconds, retry_text=retry_text)
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
        except APIRateLimitError:
            # Propaga para que a camada de interface mostre a mensagem apropriada
            raise
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

        llm = ChatGroq(model=self.model_name, temperature=self.temperature)
        
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
        except RateLimitError as e:
            msg = str(getattr(e, "body", getattr(e, "message", str(e))))
            retry_seconds, retry_text = _parse_retry_from_message(msg)
            logger.warning("Rate limit atingido em ask. retry=%s", retry_text or retry_seconds)
            raise APIRateLimitError("Limite de chamadas da API atingido.", retry_seconds=retry_seconds, retry_text=retry_text)
        except Exception as e:
            logger.exception("Erro ao gerar resposta com o agente: %s", e)
            raise
