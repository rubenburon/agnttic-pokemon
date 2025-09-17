from mcp.tools import GeminiTool

class Agent:
    def __init__(self, name, prompt, tools=None):
        self.name = name
        self.prompt = prompt
        self.tools = tools or []

    def act(self, input_text):
        # Usa la primera tool si existe
        if self.tools:
            response = self.tools[0].run(f"{self.prompt}\nUsuario: {input_text}\nDevuelve una lista de subtareas, una por línea o numeradas.")
            # Intenta extraer subtareas como lista
            subtasks = []
            for line in response.splitlines():
                line = line.strip()
                if not line:
                    continue
                # Quita numeración si existe
                if line[0].isdigit() and (line[1:3] == '. ' or line[1] == '.'):  # 1. o 1.
                    line = line.split('.', 1)[1].strip()
                subtasks.append(line)
            return subtasks if subtasks else [response]
        return [f"{self.name} recibió: {input_text}"]

class AnalystAgent(Agent):
    def __init__(self):
        super().__init__(
            name="AnalystAgent",
            prompt="""
Eres un agente analista. Tu tarea es descomponer la petición del usuario en subtareas claras y asignarlas a los agentes adecuados. Si la tarea requiere investigación, pásala al Investigador. Si requiere síntesis o redacción, pásala al Redactor.
""",
            tools=[GeminiTool()],
        )
