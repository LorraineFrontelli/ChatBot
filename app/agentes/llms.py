from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq

from app.core.config.settings import settings

llm_gemini = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.7,
    top_p=0.95,
    google_api_key=settings.GEMINI_API_KEY,
)

llm_groq = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0.7,
    api_key=settings.GROQ_API_KEY,
)

llm_especialista = llm_gemini.with_fallbacks([llm_groq])

llm_rapido = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0.0,
    api_key=settings.GROQ_API_KEY,
)

llm_guardrail = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0.0,
    api_key=settings.GROQ_API_KEY,
)

specialist_llm = llm_especialista
fast_llm = llm_rapido
