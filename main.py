from agents.analyst_agent import AnalystAgent
from agents.researcher_agent import ResearcherAgent
from agents.writer_agent import WriterAgent

# Instancia los agentes
analyst = AnalystAgent()
researcher = ResearcherAgent()
writer = WriterAgent()

# Ejemplo de flujo sencillo (handoff manual)
def main(user_input):
    # 1. Analista descompone la tarea
    subtasks = analyst.act(user_input)
    # 2. Investigador busca info para cada subtarea
    research_results = [researcher.act(task) for task in subtasks]
    # 3. Redactor sintetiza la respuesta
    final_response = writer.act("\n".join(research_results))
    return final_response

if __name__ == "__main__":
    user_input = input("Introduce tu petición: ")
    print(main(user_input))
