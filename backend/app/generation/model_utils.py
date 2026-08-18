import os
import requests

_cached_fallback = None

def get_dynamic_fallback(failed_model_name: str) -> str:
    """
    Fetches the available models from Groq API and selects the best alternative.
    Uses requests so it can be called from both sync and async contexts 
    (blocking is negligible since it runs only once on failure and is cached).
    """
    global _cached_fallback
    if _cached_fallback:
        return _cached_fallback
        
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return "groq/compound" # Ultimate fallback
        
    try:
        res = requests.get(
            "https://api.groq.com/openai/v1/models",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=10
        )
        res.raise_for_status()
        data = res.json()
        available_ids = [m["id"] for m in data.get("data", [])]
        
        # Filter out specialized audio/guard models
        exclude_keywords = ["whisper", "prompt-guard", "safeguard", "arabic"]
        text_models = [m for m in available_ids if not any(k in m.lower() for k in exclude_keywords)]
        
        # Preference ranking based on capability and token budget constraints
        # qwen is avoided if possible due to <think> block breaking parsing
        preferences = [
            "groq/compound", # Closest relative to groq/compound-mini
            "openai/gpt-oss-20b",
            "openai/gpt-oss-120b",
            "canopylabs/orpheus-v1-english",
            "allam-2-7b"
        ]
        
        for pref in preferences:
            if pref in text_models and pref != failed_model_name:
                _cached_fallback = pref
                print(f"[Dynamic Fallback] Selected best available fallback model: {_cached_fallback}")
                return _cached_fallback
                
        # If no preferred model is available, pick any valid text model
        for m in text_models:
            if m != failed_model_name:
                _cached_fallback = m
                print(f"[Dynamic Fallback] Selected arbitrary text fallback model: {_cached_fallback}")
                return _cached_fallback
                
    except Exception as e:
        print(f"[Dynamic Fallback] API request failed: {e}")
        
    # Default hardcoded fallback if all else fails
    return "groq/compound"
