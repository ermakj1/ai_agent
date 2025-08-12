def get_file_content(working_directory, file_path):
    import os

    full_working_directory = os.path.abspath(working_directory)
    full_file_path = os.path.abspath(os.path.join(working_directory, file_path))

    if(False == full_file_path.startswith(full_working_directory)):
        return f'Error: Cannot read "{file_path}" as it is outside the permitted working directory'
    
    if(False == os.path.isfile(full_file_path)):
        return f'Error: File not found or is not a regular file: "{file_path}"'
    
    try:
        from functions.config import MAX_FILE_CHARACTERS

        with open(full_file_path, 'r') as file:
            content = file.read(MAX_FILE_CHARACTERS)
            if len(content) < MAX_FILE_CHARACTERS:
                #print("returning full content  ")
                return content
            else:
                #print("returning truncated content  ")
                return f'{content}[...File "{file_path}" truncated at {MAX_FILE_CHARACTERS} characters]'        
    
    except Exception as e:
        return f"Error: {str(e)}"
    
from google.genai import types
schema_get_file_content = types.FunctionDeclaration(
    name="get_file_content",
    description="Returns the content of a file as text, constrained to the working directory.",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "file_path": types.Schema(
                type=types.Type.STRING,
                description="The path to the file to read, relative to the working directory.",
            ),
        },
    ),
)
