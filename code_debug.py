from google.genai import types
from agent import agent

from functions.get_files_info import schema_get_files_info
from functions.get_file_content import schema_get_file_content
from functions.write_file import schema_write_file
from functions.run_python import schema_run_python_file


class code_debug(agent):
    def __init__(self) -> None:
        super().__init__()
        self.system_prompt = (
            """
You are a helpful AI coding agent.

When a user asks a question or makes a request, make a function call plan. You can perform the following operations:

- List files and directories
- Read the content of files
- Write to files
- Execute Python scripts

All paths you provide should be relative to the working directory. You do not need to specify the working directory in your function calls as it is automatically injected for security reasons.

To answer questions you will probably need to look at the files in the working directory, read their content, and possibly execute Python scripts. You can also write new files if needed.

The tests.py file does not need any arguments
"""
        )

        # Tool with function declarations available to this agent
        self.available_functions = types.Tool(
            function_declarations=[
                schema_get_files_info,
                schema_get_file_content,
                schema_write_file,
                schema_run_python_file,
            ]
        )
