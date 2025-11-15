
def validate_requesty_model(model: str) -> bool:
    """Validate if model is allowed by Requesty API.
    
    Requesty blocks certain providers/models:
    - OpenAI: GPT-4o, GPT-4o-mini, GPT-5, GPT-5-mini
    - Anthropic: All Claude models
    - Google: All Gemini models
    
    Args:
        model: Model identifier (e.g., "openai/gpt-4o-mini")
        
    Returns:
        True if model is allowed, False otherwise
    """
    if "/" not in model:
        return False
        
    provider, model_name = model.split("/", 1)
    
    # Requesty blocked models (as per documentation)
    blocked_combinations = [
        ("openai", "gpt-4o"),
        ("openai", "gpt-4o-mini"),
        ("openai", "gpt-5"),
        ("openai", "gpt-5-mini"),
        ("anthropic", "claude-3-opus"),
        ("anthropic", "claude-3-sonnet"),
        ("anthropic", "claude-3-haiku"),
        ("google", "gemini-pro"),
        ("google", "gemini-pro-vision"),
    ]
    
    for blocked_provider, blocked_model in blocked_combinations:
        if provider.lower() == blocked_provider.lower() and model_name.lower().startswith(blocked_model.lower()):
            return False
            
    return True

def get_allowed_requesty_models():
    """Get list of allowed models for Requesty API.
    
    Returns:
        List of (model_id, description) tuples
    """
    return [
        ("openai/gpt-3.5-turbo", "OpenAI GPT-3.5 Turbo"),
        ("openai/gpt-4", "OpenAI GPT-4"),
        ("openai/gpt-4-turbo", "OpenAI GPT-4 Turbo"),
        ("anthropic/claude-3-5-sonnet", "Anthropic Claude 3.5 Sonnet"),
        ("anthropic/claude-3-5-haiku", "Anthropic Claude 3.5 Haiku"),
        ("google/gemini-1.5-pro", "Google Gemini 1.5 Pro"),
        ("meta/llama-3.1-70b", "Meta Llama 3.1 70B"),
        ("mistral/mistral-7b", "Mistral 7B"),
        ("cohere/command-r", "Cohere Command-R"),
    ]


async def handle_requesty_403_error(error_msg: str, model: str) -> str:
    """Handle Requesty 403 "Provider blocked by policy" errors.
    
    Args:
        error_msg: Original error message
        model: Model that caused the error
        
    Returns:
        Enhanced error message with suggestions
    """
    if "Provider blocked by policy" in error_msg:
        allowed_models = get_allowed_requesty_models()
        
        suggestions = []
        for allowed_model, description in allowed_models:
            if allowed_model.split("/")[0] == model.split("/")[0]:
                suggestions.append(f"- {allowed_model} ({description})")
        
        enhanced_msg = f"""Requesty API Error: Model '{model}' is blocked by provider policy.

SUGGESTED FIXES:
1. Update your MODEL environment variable to one of these allowed models:
{chr(10).join(suggestions) if suggestions else "- No suggestions available"}

2. Or switch to a different provider:
   - OpenAI: Set LLM_PROVIDER=openai and use OPENAI_API_KEY
   - Aether: Set LLM_PROVIDER=aether and use AETHER_API_KEY
   
3. Example fix:
   export MODEL=openai/gpt-4o-mini
   # or
   export LLM_PROVIDER=openai
   export OPENAI_API_KEY=your_key_here

Original error: {error_msg}"""
        
        return enhanced_msg
    
    return error_msg
