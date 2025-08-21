from agents.agent import Agent
from dotenv import load_dotenv
load_dotenv()

agent = Agent(settings_path="./settings/agent_settings.py")

response = agent.ask("Qual é a capital da França?")
print(response)
