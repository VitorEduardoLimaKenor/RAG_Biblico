from langchain_groq import ChatGroq
import importlib.util
from utils.biblia_functions import BibliaFunctions
from langchain_core.messages import SystemMessage, HumanMessage

class Agent:
    def __init__(self, settings_path: str, model: str):
        """
        settings_path: Caminho para o arquivo de configurações (settings).
        """
        self.settings = self._load_settings(settings_path)
        self.model = model
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

    def ask(self, question: str):
        """
        Faz uma pergunta ao modelo de linguagem com base no prompt fornecido.
        """
        model = ChatGroq(model=self.model, temperature=self.settings.TEMPERATURE)

        versiculos = self.biblia.busca_versiculo(query=question, n_results=self.settings.NUM_VERSICULOS)

        response = model.invoke([
            SystemMessage(content=self.settings.SYSTEM_INSTRUCTION_TEMPLATE.format(versiculos=versiculos)),
            HumanMessage(content=question)
        ])

        return response.content
