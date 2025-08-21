from tools.agent_tools import build_llm
import importlib.util

class Agent:
    def __init__(self, settings_path: str):
        """
        settings_path: Caminho para o arquivo de configurações (settings).
        """
        self.settings = self._load_settings(settings_path)

    def _load_settings(self, path: str):
            """Carrega dinamicamente um módulo de settings a partir de um caminho."""
            spec = importlib.util.spec_from_file_location("settings", path)
            settings = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(settings)
            return settings
    
    def ask(self, prompt: str):
        """
        Faz uma pergunta ao modelo de linguagem com base no prompt fornecido.
        """
        llm = build_llm(model=self.settings.MODEL, temperature=self.settings.TEMPERATURE)
        response = llm.invoke(prompt)
        return response.content

