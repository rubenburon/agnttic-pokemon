from mcp.tools import GeminiTool
from agents.analyst_agent import Agent

class WriterAgent(Agent):
    def __init__(self):
        super().__init__(
            name="WriterAgent",
            prompt="""
Eres un agente redactor. Tu tarea es sintetizar la información proporcionada y generar una respuesta clara y concisa para el usuario.
""",
            tools=[GeminiTool()],
        )
