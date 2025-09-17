from mcp.tools import GeminiTool
from agents.analyst_agent import Agent

class ResearcherAgent(Agent):
    def __init__(self):
        super().__init__(
            name="ResearcherAgent",
            prompt="""
Eres un agente investigador. Tu tarea es buscar información relevante usando la herramienta Gemini y devolver los resultados al agente que lo solicitó.
""",
            tools=[GeminiTool()],
        )
