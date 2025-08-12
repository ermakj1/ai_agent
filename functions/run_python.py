def run_python_file(working_directory, file_path, args=[]):
    import os
    import subprocess

    full_working_directory = os.path.abspath(working_directory)
    full_file_path = os.path.abspath(os.path.join(working_directory, file_path))

    if not full_file_path.startswith(full_working_directory):
        return f'Error: Cannot execute "{file_path}" as it is outside the permitted working directory'
    
    if not os.path.isfile(full_file_path):
        print(full_file_path)
        return f'Error: File "{file_path}" not found'

    if not file_path.endswith('.py'):
        return f'Error: "{file_path}" is not a Python file'
    
    try:
        result = subprocess.run(
            ['python', full_file_path] + args,
            cwd=full_working_directory,
            capture_output=True,
            text=True
        )

        output = ""

        if result.stdout:
            output += f"STDOUT: {result.stdout}\n"
        if result.stderr:
            output += f"STDERR: {result.stderr}\n"
        if result.returncode != 0:
            output += f"Process exited with code {result.returncode}\n"
        if output == "":
            return "No output produced"
        
        return output
            
    except Exception as e:
        return f"Error executing Python file: {e}"
    
from google.genai import types
schema_run_python_file = types.FunctionDeclaration(
    name="run_python_file",
    description="Executes a Python file in the working directory with optional arguments.",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "file_path": types.Schema(
                type=types.Type.STRING,
                description="The path to the Python file to execute, relative to the working directory.",
            ),
            "args": types.Schema(
                type=types.Type.ARRAY,
                items=types.Schema(
                    type=types.Type.STRING,
                    description="Optional arguments to pass to the Python script."
                ),
                description="Optional arguments to pass to the Python script.",
            ),
        },
        required=["file_path"],
    )
)