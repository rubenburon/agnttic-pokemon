# Construyendo agentes con Smol Agents

Este repo implementa un caso de uso de multiagentes en smol agents de Hugging Face.

El proceso de creación de agentes lo vamos a realizar de manera iterativa en los siguientes archivos:
 - 01 smolagent.py: Un único agente en el framework, utiliza el flujo ReAct implementado por defecto, las herramientas por defecto del framework e incluye una config básica y un prompt muy sencillo que le va a pedir usar las herramientas para consultar por internet.
 - 02 smolagent.py: Un único agente con una herramienta implementada como una función para leer archivos de Excel. Ilustra los cambios que hay que hacer en el agente para poder utilizar esta función.
 - 03 smolagent_langfuse.py: Añadimos una configuración básica en langfuse para monitorizar en tiempo real las métricas y observar el razonamiento del agente.
 - 03 smolagent.py: Añade un system prompt para modificar la personalidad de un jugador de pokemon al agente. Además, añadimos un evaluador para comprobar que la salida del smol agent es correcta.
 - 04 smolagentmcp.py: Utiliza un mpc local que nos permite obtener todos los movimientos y puntaciones que puede tener un determinado pokemon. Implementa la llamada por mcp, pero utiliza la entrada / salida por consola.
 - 05 smolagentmcp.py: Utiliza la funcionalidad del framework para utilizar entre uno y tres subagentes.
 - 06 smolagentmcp.py: Implementamos un patrón de comunicación con un agente principal y dos subagentes que compiten entre sí.