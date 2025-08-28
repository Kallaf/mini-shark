import os
import google.generativeai as genai
from mock_model import MockLLM
from utils import extract_json
from dotenv import load_dotenv

def setup_llm():
    load_dotenv()
    useMockLLM = os.getenv("USE_MOCK_LLM")
    if useMockLLM == "True":
        return MockLLM()
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found in .env file.")
    genai.configure(api_key=api_key)
    return genai.GenerativeModel('gemini-1.5-flash')

def get_shark_response(model, prompt):
    response = model.generate_content(prompt)
    return extract_json(response.text)
