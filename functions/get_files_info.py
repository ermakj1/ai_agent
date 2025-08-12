import os
from google.genai import types

def get_files_info(working_directory, directory="."):
    working_directory = os.path.abspath(working_directory)
    fullpath = os.path.join(working_directory, directory)
    fullpath = os.path.abspath(fullpath)

    #check fullpath is in working_directory
    if not fullpath.startswith(working_directory):
        return f'Error: Cannot list "{directory}" as it is outside the permitted working directory'
        
    if not os.path.isdir(fullpath):
        return f'Error: "{directory}" is not a directory'
    try:
        fullstring = ""
        for file in os.listdir(fullpath):
            fullstring += f"- {file}: file_size={os.path.getsize(os.path.join(fullpath, file))} bytes, is_dir={os.path.isdir(os.path.join(fullpath, file))}\n"
        
        return fullstring
    except Exception as e:
        return f"Error: {str(e)}"
    
schema_get_files_info = types.FunctionDeclaration(
    name="get_files_info",
    description="Lists files in the specified directory along with their sizes, constrained to the working directory.",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "directory": types.Schema(
                type=types.Type.STRING,
                description="The directory to list files from, relative to the working directory. If not provided, lists files in the working directory itself.",
            ),
        },
    ),
)