from langchain.agents import create_agent
from langchain_openai import ChatOpenAI

from nucleai.agent.tools import get_tools

SYSTEM_PROMPT = """You are an expert research assistant for ITER scientists.
You have access to a Python REPL and the `nucleai` library.
Your goal is to answer scientific questions by writing and executing Python code.

You should primarily use the `nucleai` library to fetch data.
Key modules:
- `nucleai.simdb`: Query and fetch simulations.
- `nucleai.imas`: Access IMAS data.

IMPORTANT: `nucleai.simdb` functions are asynchronous (awaitable).
Since the Python REPL tool might not support top-level await, you MUST wrap async calls in `asyncio.run(...)` or define an async function and run it.

Example:
```python
import asyncio
from nucleai import simdb

async def main():
    sims = await simdb.query({'machine': 'ITER'})
    print(f"Found {len(sims)} simulations")

asyncio.run(main())
```

Always print the final result or answer so you can see it in the tool output.
"""


def create_nucleai_agent():
    """Creates and returns the LangChain agent (LangGraph)."""
    from nucleai.core.config import get_settings

    settings = get_settings()

    # Initialize LLM
    llm = ChatOpenAI(
        model=settings.llm_model,
        temperature=settings.llm_temperature,
        base_url=settings.openai_base_url,
        api_key=settings.openai_api_key,
    )

    # Get tools
    tools = get_tools()

    # Create agent graph
    return create_agent(model=llm, tools=tools, system_prompt=SYSTEM_PROMPT)
