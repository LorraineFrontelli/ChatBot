from langchain.agents import create_agent

from .router_prompts import ROUTER_PROMPT
from ..llms import fast_llm

router_app = create_agent(
    model=fast_llm,
    system_prompt=ROUTER_PROMPT,
)
