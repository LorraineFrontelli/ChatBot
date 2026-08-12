from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from dotenv import load_dotenv
import os

load_dotenv()

llm_gemini = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.7,
    top_p=0.95,
    google_api_key=os.getenv("GEMINI_API_KEY"),
)

llm_groq = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0.7,
    api_key=os.getenv("GROQ_API_KEY"),
)

llm_especialista = llm_gemini.with_fallbacks([llm_groq])

llm_rapido = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0.0,
    api_key=os.getenv("GROQ_API_KEY"),
)

specialist_llm = llm_especialista
fast_llm = llm_rapido
