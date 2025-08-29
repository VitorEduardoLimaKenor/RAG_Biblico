from langchain_groq import ChatGroq
import importlib.util
from utils.biblia_functions import BibliaFunctions
from langchain_core.messages import SystemMessage, HumanMessage

class Agent:
    def __init__(self, settings_path: str, model: str):
        """
        settings_path: Caminho para o arquivo de configurações (settings).
        model: Nome do modelo de linguagem a ser utilizado.
        """
        self.settings = self._load_settings(settings_path)
        self.model = ChatGroq(model=model, temperature=self.settings.TEMPERATURE)
        self.biblia = BibliaFunctions(
            biblia_path=self.settings.BIBLIA_PATH,
            chroma_path=self.settings.CHROMA_PATH,
            collection_name=self.settings.COLLECTION_NAME
        )
        self.biblia.carregar_biblia()

    def _load_settings(self, path: str):
            """Carrega dinamicamente um módulo de settings a partir de um caminho."""
            spec = importlib.util.spec_from_file_location("settings", path)
            settings = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(settings)
            return settings

    def analisar_pergunta(self, question: str):
        prompt = f"""
        Aja como um avaliador de perguntas bíblicas. Sua tarefa é analisar a pergunta fornecida e decidir se:

        1. A pergunta faz sentido, não é ofensiva e pode ter algum ensinamento bíblico aplicado → nesse caso retorne apenas "true".
        2. A pergunta não faz sentido, é ofensiva, ou não possui qualquer ligação com princípios bíblicos → nesse caso retorne apenas "false".
        ---
        
        ### Importante:
        - Não explique sua resposta.
        - Não dê justificativas.
        - O resultado deve ser estritamente "true" ou "false".
        ---

        ### Exemplos:
        Pergunta: "Como a Bíblia ensina a perdoar quem nos fez mal?"
        Resposta: true

        Pergunta: "Quais princípios bíblicos podem me ajudar a lidar com a ansiedade?"
        Resposta: true

        Pergunta: "Quantos planetas existem no sistema solar?"
        Resposta: false

        Pergunta: "Qual é o melhor processador de computador em 2025?"
        Resposta: false

        Pergunta: "Por que Deus permite o sofrimento no mundo?"
        Resposta: true

        Pergunta: "Me dê dicas para ganhar na loteria amanhã."
        Resposta: false
        ---

        ### Agora analise a pergunta do usuário:
        Pergunta do usuário: {question}
        """
        response = self.model.invoke(prompt)
        return response.content

    def extrair_semantica(self, question: str):
        prompt = f"""
        Aja como um especialista em estudos bíblicos e em recuperação semântica de informações. Sua tarefa é reescrever a pergunta do usuário de forma clara, direta e otimizada para melhorar a busca semântica em um banco vetorial de versículos da Bíblia.

        Instruções:
            - Concentre-se nos termos centrais da pergunta, eliminando palavras de polidez, ambiguidades ou trechos irrelevantes.
            - Transforme a pergunta em uma forma que enfatize os conceitos ou temas bíblicos principais.
            - Use linguagem objetiva, destacando possíveis palavras-chave ou sinônimos relevantes que poderiam aparecer em versículos bíblicos.
            - Mantenha a reescrita fiel à intenção original do usuário.

        Entrada do usuário: {question}
        Saída esperada: Pergunta reescrita de forma otimizada para busca semântica em versículos bíblicos.
        """

        response = self.model.invoke(prompt)
        return response.content

    def ask(self, question: str):
        """
        Faz uma pergunta ao modelo de linguagem com base no prompt fornecido.
        """
        analise = self.analisar_pergunta(question)
        if "false" in analise.lower():
            return "Desculpe, não posso ajudar com essa pergunta. Por favor, faça uma pergunta relacionada a ensinamentos bíblicos."

        pergunta_semantica = self.extrair_semantica(question)

        versiculos = self.biblia.busca_versiculo(query=pergunta_semantica, n_results=self.settings.NUM_VERSICULOS)

        response = self.model.invoke([
            SystemMessage(content=self.settings.SYSTEM_INSTRUCTION_TEMPLATE.format(versiculos=versiculos)),
            HumanMessage(content=question)
        ])

        return response.content
