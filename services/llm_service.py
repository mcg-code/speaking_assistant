import ollama
from typing import List, Dict

def chat(model_name: str, messages: List[Dict[str, str]]) -> str:
    """
    Sends a conversation history to Ollama and returns the AI response.
    
    Args:
        model_name: The name of the local Ollama model to use.
        messages: A list of message dictionaries (role, content).
        
    Returns:
        The response content string.
    """
    try:
        response = ollama.chat(model=model_name, messages=messages)
        return response['message']['content']
    except Exception as e:
        raise ConnectionError(f"Error communicating with Ollama: {e}")

def get_installed_models() -> List[str]:
    """
    Retrieves the list of installed models from the local Ollama instance.
    """
    try:
        response = ollama.list()
        # The 'models' key contains a list of model dictionaries
        return [model['model'] for model in response.get('models', [])]
    except Exception:
        return []
