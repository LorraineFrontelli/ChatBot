from langchain.agents import create_agent

from app.memory.tools import TOOLS_MEMORIA

from .router_prompts import ROUTER_PROMPT
from ..llms import fast_llm

router_app = create_agent(
    model=fast_llm,
    system_prompt=ROUTER_PROMPT,
    tools=TOOLS_MEMORIA,
)
