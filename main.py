import os
import sys
from dotenv import load_dotenv
from google import genai
from google.genai import types

from functions.get_files_info import *
from functions.get_file_content import *
from functions.write_file import *
from functions.run_python import *

def main():
    print("Hello from ai-agent!")

    system_prompt = """
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

    # Load environment variables from .env file
    if False == load_dotenv("ai_key.env"):
        raise FileNotFoundError(".env file not found. Please create a .env file with your API key.")
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is not set.")

    client = genai.Client(api_key=api_key)
    
    
    if len(sys.argv) > 1:
        prompt = sys.argv[1]
    else:
        print("No prompt provided.")
        exit (1)

    verbose = False
    for arg in sys.argv[2:]:
        if arg == "--verbose":
            print("Verbose mode enabled.")
            verbose = True


    messages = [
        types.Content(role="user", parts=[types.Part(text=prompt)]),
    ]

    system_instruction = types.Content(role="system", parts=[types.Part(text=system_prompt)])

    available_functions = types.Tool(
        function_declarations=[
            schema_get_files_info,
            schema_get_file_content,
            schema_write_file,
            schema_run_python_file,
        ]
    )

    config=types.GenerateContentConfig(
        tools=[available_functions], system_instruction=system_prompt
    )

    MAX_LOOPS = 20
    current_loop = 0

    while current_loop < MAX_LOOPS:
        try:
            current_loop += 1

            # call to the gemini model
            response = client.models.generate_content(
                model="gemini-2.0-flash-001", 
                contents=messages, 
                config=config)

            # read response candidates from the model (append model turn so function call context is preserved)
            if response.candidates:
                for candidate in response.candidates:
                    if candidate.content is not None:
                        messages.append(candidate.content)

            # loop through function calls if any
            function_response_parts = []
            if response.function_calls:
                for function_call_part in response.function_calls:
                    function_call_result_content = call_function(function_call_part, verbose=verbose)
                    # Each call_function returns a Content with one Part (function_response)
                    if function_call_result_content and function_call_result_content.parts:
                        fr_part = function_call_result_content.parts[0]
                        function_response_parts.append(fr_part)
                # Append a SINGLE user message containing all function response parts (must 1:1 with function calls of previous model turn)
                if function_response_parts:
                    messages.append(
                        types.Content(
                            role="tool",
                            parts=function_response_parts
                        )
                    )
                    continue

            # check if the model response contains a response text (only when no function call round)
            if response.text:
                print("Assistant response: ", response.text)
                break

            # print prompt tokens and response tokens
            if verbose:
                print("User prompt:", prompt)
                if response.usage_metadata is not None:
                    print("Prompt tokens:", getattr(response.usage_metadata, "prompt_token_count", "N/A"))
                    print("Response tokens:", getattr(response.usage_metadata, "candidates_token_count", "N/A"))
                else:
                    print("Prompt tokens: N/A")
                    print("Response tokens: N/A")
        except Exception as e:
            print(f"Error during processing: {e}")
            print( e.with_traceback(sys.exc_info()[2]))
            break
    
    #end loop

    if verbose:
        print("END: Total messages:", len(messages))
        for message in messages:
            if message.parts and len(message.parts) > 0:
                if hasattr(message.parts[0], "text") and message.parts[0].text is not None:
                    print(f"{message.role}: {message.parts[0].text}")
                elif hasattr(message.parts[0], "function_response"):
                    print(f"{message.role}: {message.parts[0].function_response}")
                else:
                    print(f"{message.role}: [Unknown part type]")
            else:
                print(f"{message.role}: [No parts]")



def call_function(function_call_part, verbose=False):
    function_name = function_call_part.name
    args = function_call_part.args

    print(f"Calling function: {function_name} with args: {args}")

    function_result = None

    if function_name == "get_files_info":
        function_result = get_files_info("./calculator", **args)
    elif function_name == "get_file_content":
        function_result = get_file_content("./calculator", **args)
    elif function_name == "write_file":
        function_result = write_file("./calculator", **args)
    elif function_name == "run_python_file":
        function_result = run_python_file("./calculator", **args)
    else:
        return types.Content(
            role="tool",
            parts=[
                types.Part.from_function_response(
                    name=function_name,
                    response={"error": f"Unknown function: {function_name}"},
                )
            ],
        )  

    return types.Content(
        role="tool",
        parts=[
            types.Part.from_function_response(
                name=function_name,
                response={"result": function_result},
            )
        ],
    )

if __name__ == "__main__":
    main()
