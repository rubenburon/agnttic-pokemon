import google.generativeai as genai

class GeminiTool:
    def __init__(self, api_key=None, model="gemini-2.5-flash"):
        self.api_key = api_key or "AIzaSyALmQ9eqDaiiaj0YOCmHbVDvc6QdFUnUJY"
        self.model = model
        genai.configure(api_key=self.api_key)

    def run(self, prompt: str) -> str:
        response = genai.generate_content(self.model, prompt)
        return response.text if hasattr(response, 'text') else str(response)

# Puedes añadir más tools aquí si lo necesitas
