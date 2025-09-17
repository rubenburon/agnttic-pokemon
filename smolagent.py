import os

from dotenv import load_dotenv

from smolagents import (
    CodeAgent,
    ToolCallingAgent,
    DuckDuckGoSearchTool, 
    InferenceClientModel,
    GoogleSearchTool,
    VisitWebpageTool, 
    tool,
    LiteLLMModel,
)

load_dotenv()
#langfuse = Langfuse()

# from opentelemetry.sdk.trace import TracerProvider

# from openinference.instrumentation.smolagents import SmolagentsInstrumentor
# from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
# from opentelemetry.sdk.trace.export import SimpleSpanProcessor

# trace_provider = TracerProvider()
# trace_provider.add_span_processor(SimpleSpanProcessor(OTLPSpanExporter()))

# SmolagentsInstrumentor().instrument(tracer_provider=trace_provider)


def create_agent():
    model = LiteLLMModel(model_id="gemini/gemini-2.0-flash-exp",
                     api_key=os.getenv("GEMINI_API_KEY"))

    # with ToolCollection.from_mcp(server_parameters, trust_remote_code=True) as tool_collection:
    agent = CodeAgent(
        tools=[
            #*tool_collection.tools,
        ],
        model=model, 
        additional_authorized_imports=["time","pandas","json","numpy"],
      #  step_callbacks=[load_images],
        planning_interval=3,
        max_steps=10,
        add_base_tools=True)
    return agent


if __name__ == "__main__":
    load_dotenv()
    agent = create_agent()
    try:    
        output = agent.run("What's the current weather in Granada?")
    except Exception as e:
        print(f"Error running agent: {e}")
        output = f"Error running agent: {e}"