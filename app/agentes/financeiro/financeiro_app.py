from langchain.agents import create_agent

from app.memory.tools import TOOLS_MEMORIA

from ..llms import specialist_llm
from .financeiro_prompts import FINANCIAL_PROMPT
from .tools import TOOLS

financial_app = create_agent(
    model=specialist_llm, system_prompt=FINANCIAL_PROMPT, tools=TOOLS + TOOLS_MEMORIA
)
