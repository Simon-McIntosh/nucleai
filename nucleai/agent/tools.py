from langchain_core.tools import Tool
from langchain_experimental.utilities import PythonREPL


def get_tools():
    """Returns a list of tools for the agent.

    Includes a Python REPL for executing code.
    """
    python_repl = PythonREPL()

    # We can customize the description to encourage using nucleai
    repl_tool = Tool(
        name="python_repl",
        description="A Python shell. Use this to execute python commands. Input should be a valid python command. If you want to see the output of a value, you should print it out with `print(...)`.",
        func=python_repl.run,
    )

    return [repl_tool]
