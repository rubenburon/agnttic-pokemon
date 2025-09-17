import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

class GeminiTool:
    def __init__(self, api_key=None, model="gemini-2.5-flash"):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model_name = model
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(model_name=f"models/{self.model_name}")

    def run(self, prompt: str) -> str:
        response = self.model.generate_content(prompt)
        return response.text if hasattr(response, 'text') else str(response)

# Puedes añadir más tools aquí si lo necesitas
