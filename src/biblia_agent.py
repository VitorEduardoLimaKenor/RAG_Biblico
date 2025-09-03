from langchain_groq import ChatGroq
import importlib.util
from src.utils.biblia_functions import BibliaFunctions
from src.utils.obra_functions import ObrasFunctions
from langchain.prompts import ChatPromptTemplate
from langchain.agents import Tool
from langgraph.prebuilt import create_react_agent


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
        self.easton = ObrasFunctions(
            obra_path="./src/data/obras_auxiliares/dicionario_easton.json",
            chroma_path="./src/data/chroma_db",
            collection_name="easton"
        )
        self.easton.load_collection()
        self.naves = ObrasFunctions(
            obra_path="./src/data/obras_auxiliares/naves_topical.json",
            chroma_path="./src/data/chroma_db",
            collection_name="naves"
        )
        self.naves.load_collection()

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
    
    def buscar_versiculos_semantica(self, query: str):
        return self.biblia.busca_versiculo(query=query, n_results=5)

    def buscar_contexto_historico(self, query: str):
        return self.easton.semantic_search(query=query, n_results=1)

    def buscar_por_topico(self, query: str):
        return self.naves.semantic_search(query=query, n_results=3)

    def buscar_na_biblia_json(self, livro: str, capitulo: int):
        return self.biblia.buscar_por_referencia(livro=livro, capitulo=capitulo)

    def ask(self, question: str):
        """
        Faz uma pergunta ao modelo de linguagem com base no prompt fornecido.
        """
        analise = self.analisar_pergunta(question)
        if "false" in analise.lower():
            return "Desculpe, não posso ajudar com essa pergunta. Por favor, faça uma pergunta relacionada a ensinamentos bíblicos."
        
        tools = [
            Tool(
                name="Busca_Versiculos",
                func=self.buscar_versiculos_semantica,
                description="Use para encontrar versículos que respondam perguntas diretas."
            ),
            Tool(
                name="Busca_Tematica_Naves",
                func=self.buscar_por_topico,
                description="Use para encontrar versículos relacionados a um tema (como amor, fé, perdão)."
            ),
            Tool(
                name="Busca_Historica_Easton",
                func=self.buscar_contexto_historico,
                description="Use para responder perguntas históricas, contextuais ou biográficas da Bíblia."
            ),
            Tool(
                name="Busca_Estrutural_Biblia_JSON",
                func=self.buscar_na_biblia_json,
                description="Use para buscar informações literais e históricas diretamente no texto bíblico, por exemplo 'Quantos anos viveu Adão?' ou 'Quem foi pai de Jacó?'."
            )
        ]

        # Não precisa puxar o prompt do hub nem passar state_modifier
        agent_executor = create_react_agent(self.model, tools)

        response = agent_executor.invoke(
            {"messages": [
                {"role": "system", "content": self.settings.SYSTEM_INSTRUCTION_TEMPLATE},
                {"role": "user", "content": question}
            ]}
        )

        return response["messages"][-1].content
