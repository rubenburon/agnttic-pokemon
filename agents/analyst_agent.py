from mcp.tools import GeminiTool

class Agent:
    def __init__(self, name, prompt, tools=None):
        self.name = name
        self.prompt = prompt
        self.tools = tools or []

    def act(self, input_text):
        # Simple reasoning and action: usa la primera tool si existe
        if self.tools:
            return self.tools[0].run(f"{self.prompt}\nUsuario: {input_text}")
        return f"{self.name} recibió: {input_text}"

class AnalystAgent(Agent):
    def __init__(self):
        super().__init__(
            name="AnalystAgent",
            prompt="""
Eres un agente analista. Tu tarea es descomponer la petición del usuario en subtareas claras y asignarlas a los agentes adecuados. Si la tarea requiere investigación, pásala al Investigador. Si requiere síntesis o redacción, pásala al Redactor.
""",
            tools=[GeminiTool()],
        )
