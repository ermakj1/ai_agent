from google.genai import types

class agent:
    """Base agent interface.

    Subclasses must expose:
      - system_prompt: str
      - available_functions: types.Tool
    """

    def __init__(self) -> None:
        # Defaults; subclasses should override
        self.system_prompt: str = ""
        self.available_functions: types.Tool = types.Tool(function_declarations=[])
