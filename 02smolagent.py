import os
from dotenv import load_dotenv
# formato del archivo .env:
# GEMINI_API_KEY=xxxxxxxxxxxxx

# Importar la herramienta para leer excel:
from tools.excelTool import (
    read_excel_file,
    write_excel
)


from smolagents import (
    CodeAgent,
    ToolCollection,
    LiteLLMModel, # para usar Gemini (entre otros)
    OpenAIServerModel, # para usar OpenAI
    InferenceClientModel # para usar la api serverless de Hugging Face

)




def create_agent():
    # Configuración del agente.
    # Se pueden usar varios modelos y se cargan de manera diferente:
    # para usar Gemini:
    model = LiteLLMModel(model_id="gemini/gemini-2.0-flash-exp",
                     api_key=os.getenv("GEMINI_API_KEY"))
    # para usar algún modelo de OpenAI (pon la API_KEY en el archivo .env)
    # Acuérdate de poner también el import correspondiente de OpenAIServerModel
    # model = OpenAIServerModel(model_id="gpt-4o")
    # para usar algún modelo del hub de Huggin Face y usar su Api de inferencia Serverless
    # model = InferenceClientModel(model_id="Qwen/Qwen2.5-Coder-32B-Instruct")

    
    agent = CodeAgent(
        tools=[
            # aquí van la tool
            read_excel_file,write_excel
        ],
        model=model, 
        # estos son los imports que puede usar el agente en el código python que genera.
        # estas librerías las tienes que tener importadas en tu requirements.txt
        additional_authorized_imports=["time","pandas","json","numpy"],

        # Cada cuántos pasos va a revisar el plan:
        planning_interval=3,
        # número máximo de pasos que va a realizar el agente
        # si llega a este número de pasos, va a parar aunque no consiga implementar la tarea.
        max_steps=10,
        # incluye las tools base de smolagents que le permiten buscar por internet y otras tareas.
        add_base_tools=True)
    return agent


if __name__ == "__main__":
    # carga las variables de entorno
    load_dotenv()
    # donde se encuentra el CA para el querido ZSCALER
    #ca_cert_path = os.getenv('CA_BUNDLE')
    # configurar la librería requests para que utilice el CA que hemos especificado.

   # os.environ['PYTHONHTTPSVERIFY']='0'

    agent = create_agent()
    try:    
        # cambiamos el user prompt para pedirle que escriba en un excel  con varias columnas los personajes principales de Pokemon, una descripción y el tipo:
        user_prompt = "I want to get in Excel file format the most well-known Pokemons with a description and their type. I want this specific format of columns: Name, Description, Type."
        output = agent.run(user_prompt)
    except Exception as e:
        print(f"Error running agent: {e}")
        output = f"Error running agent: {e}"