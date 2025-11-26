"""
LLM API Integration Script
Supports different types of context and prompt inputs
"""
import os
import requests
import json
from typing import Dict, Optional
from dotenv import load_dotenv
import traceback

load_dotenv()

# Load LLM API configuration from environment variables
LLM_API_URL = os.getenv("LLM_API_URL", "https://api.openai.com/v1/chat/completions")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-3.5-turbo")


# Define different types of Context
# TODO: Add your context types here
# Format: {
#     "context_type_name": {
#         "name": "Display Name",
#         "system_prompt": "System prompt for this context type"
#     }
# }
CONTEXT_TYPES: Dict[str, Dict[str, str]] = {}


def add_context_type(context_type: str, name: str, system_prompt: str) -> None:
    """
    Add a new context type to the CONTEXT_TYPES dictionary
    
    Args:
        context_type (str): The key identifier for this context type
        name (str): Display name for this context type
        system_prompt (str): System prompt to use for this context type
    """
    CONTEXT_TYPES[context_type] = {
        "name": name,
        "system_prompt": system_prompt
    }


def call_llm_api(
    prompt: str,
    context_type: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
    additional_context: Optional[str] = None,
    system_prompt: Optional[str] = None
) -> Dict:
    """
    Call LLM API and return output based on different context types
    
    Args:
        prompt (str): User input prompt
        context_type (str, optional): Context type identifier. If provided, will use the 
                                      system_prompt from CONTEXT_TYPES. If None, will use 
                                      system_prompt parameter or default behavior.
        temperature (float): Randomness of generated text, range 0-1, default 0.7
        max_tokens (int, optional): Maximum number of tokens, default None (decided by API)
        additional_context (str, optional): Additional context information to append to system prompt
        system_prompt (str, optional): Custom system prompt. If provided, will override context_type.
                                      If both are None, no system prompt will be used.
    
    Returns:
        Dict: Dictionary containing the following fields:
            - success (bool): Whether the call was successful
            - output (str): Text content returned by LLM (if successful)
            - error (str, optional): Error message (if failed)
            - usage (dict, optional): Token usage information (if API returns it)
    
    Example:
        >>> result = call_llm_api("What is the best time to take medicine?", context_type="drug")
        >>> if result["success"]:
        >>>     print(result["output"])
    """
    # Determine system prompt
    final_system_prompt = None
    
    if system_prompt:
        # Use provided system_prompt directly
        final_system_prompt = system_prompt
    elif context_type:
        # Use system_prompt from CONTEXT_TYPES
        if context_type not in CONTEXT_TYPES:
            return {
                "success": False,
                "error": f"Unsupported context type: {context_type}. Available types: {list(CONTEXT_TYPES.keys())}"
            }
        context_config = CONTEXT_TYPES[context_type]
        final_system_prompt = context_config["system_prompt"]
    
    # Append additional context if provided
    if final_system_prompt and additional_context:
        final_system_prompt = f"{final_system_prompt}\n\nAdditional Context:\n{additional_context}"
    elif additional_context:
        # If no system prompt but additional context, use it as system prompt
        final_system_prompt = additional_context
    
    # Build request messages
    messages = []
    if final_system_prompt:
        messages.append({"role": "system", "content": final_system_prompt})
    messages.append({"role": "user", "content": prompt})
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LLM_API_KEY}"
    }
    
    payload = {
        "model": LLM_MODEL,
        "messages": messages,
        "temperature": temperature
    }
    
    if max_tokens:
        payload["max_tokens"] = max_tokens
    
    try:
        # Send request
        response = requests.post(
            LLM_API_URL,
            headers=headers,
            json=payload,
            timeout=30
        )
        
        # Check response status
        if response.status_code == 200:
            data = response.json()
            
            # Extract reply content
            output = data["choices"][0]["message"]["content"]
            
            # Extract usage information (if exists)
            usage = data.get("usage", {})
            
            return {
                "success": True,
                "output": output,
                "usage": usage
            }
        else:
            error_msg = f"API request failed with status code: {response.status_code}"
            try:
                error_detail = response.json()
                error_msg += f", details: {error_detail}"
            except:
                error_msg += f", response: {response.text}"
            
            return {
                "success": False,
                "error": error_msg
            }
            
    except requests.exceptions.Timeout:
        return {
            "success": False,
            "error": "Request timeout, please try again later"
        }
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": f"Network request error: {str(e)}"
        }
    except Exception as e:
        print(f"❌ [LLM API Error] {e}")
        traceback.print_exc()
        return {
            "success": False,
            "error": f"Unknown error: {str(e)}"
        }


def get_available_context_types() -> list:
    """
    Get all available context types
    
    Returns:
        list: List of context type identifiers
    """
    return list(CONTEXT_TYPES.keys())


def get_context_info(context_type: str) -> Dict:
    """
    Get detailed information for a specific context type
    
    Args:
        context_type (str): Context type identifier
    
    Returns:
        Dict: Context information containing 'name' and 'system_prompt', 
              or empty dict if context_type doesn't exist
    """
    if context_type not in CONTEXT_TYPES:
        return {}
    return CONTEXT_TYPES[context_type]


if __name__ == "__main__":
    # Test example
    print("=" * 50)
    print("LLM API Test")
    print("=" * 50)
    
    # Test 1: Basic call without context type
    print("\n1. Basic call test:")
    result = call_llm_api("Hello, how are you?")
    if result["success"]:
        print(f"✅ Success: {result['output']}")
    else:
        print(f"❌ Failed: {result['error']}")
    
    # Test 2: Call with custom system prompt
    print("\n2. Custom system prompt test:")
    result = call_llm_api(
        "What is the capital of France?",
        system_prompt="You are a helpful assistant."
    )
    if result["success"]:
        print(f"✅ Success: {result['output']}")
    else:
        print(f"❌ Failed: {result['error']}")
    
    # Test 3: Call with context type (if any defined)
    print("\n3. Context type test:")
    available_types = get_available_context_types()
    if available_types:
        result = call_llm_api("Test prompt", context_type=available_types[0])
        if result["success"]:
            print(f"✅ Success: {result['output']}")
        else:
            print(f"❌ Failed: {result['error']}")
    else:
        print("ℹ️  No context types defined yet. Use add_context_type() to add them.")
    
    # Display available context types
    print("\n4. Available Context Types:")
    if CONTEXT_TYPES:
        for ctx_type in get_available_context_types():
            info = get_context_info(ctx_type)
            print(f"  - {ctx_type}: {info.get('name', 'N/A')}")
    else:
        print("  No context types defined. Use add_context_type() to add them.")
