from langchain.agents import create_agent

from app.memory.tools import TOOLS_MEMORIA

from ..llms import specialist_llm
from .agenda_prompts import AGENDA_PROMPT

agenda_app = create_agent(model=specialist_llm, system_prompt=AGENDA_PROMPT, tools=TOOLS_MEMORIA)
