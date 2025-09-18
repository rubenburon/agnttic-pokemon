import os
from dotenv import load_dotenv
from smolagents import (
    CodeAgent,
    OpenAIServerModel,
    ToolCallingAgent,
    ToolCollection,
    DuckDuckGoSearchTool, 
    InferenceClientModel,
    GoogleSearchTool,
    VisitWebpageTool, 
    tool,
    LiteLLMModel,
    MCPClient
)
from mcp import StdioServerParameters

def build_agents():
    #"deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B"
    #deepseek-ai/DeepSeek-R1-0528
    model = OpenAIServerModel(model_id="gpt-4o")
    #model = InferenceClientModel(model_id="Qwen/Qwen2.5-Coder-32B-Instruct") #Qwen/Qwen2.5-Coder-32B-Instruct")
    server_parameters = StdioServerParameters(
    command="uvx",
    args=["--quiet", "pubmedmcp@0.1.3"],
    env={"UV_PYTHON": "3.12", **os.environ},
    )

    try:
        print
        mcp_client = MCPClient(server_parameters)
        print("MCPClient initialized successfully.")
        tools = mcp_client.get_tools()
        print(f"Retrieved {len(tools)} tools from MCPClient.")

        agent = CodeAgent(
            tools=tools,
            model=model, 
            #additional_authorized_imports=["time","pandas","json","numpy","markdownify","requests","re","openpyxl","beautifulsoup4"],
            planning_interval=3,
            max_steps=10,
            add_base_tools=True)
        
        result = agent.run("What are the recent therapeutic approaches for Alzheimer's disease?")

        # Process the result as needed
        print(f"Agent response: {result}")
    except Exception as e:
        print(f"Failed to initialize MCPClient: {e}")
    finally:
        mcp_client.disconnect()
  
  

    return result



if __name__ == "__main__":
    load_dotenv()
    build_agents()