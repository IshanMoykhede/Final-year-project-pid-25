import os
import logging
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Cache client instances to avoid repeated initialization
_client = None
_current_provider = None

def get_llm_provider() -> str:
    """Returns current configured LLM provider: 'ollama' or 'groq'."""
    return os.getenv("LLM_PROVIDER", "ollama").strip().lower()

def get_llm_client():
    """
    Returns an API client compatible with OpenAI standard chat completions.
    - If LLM_PROVIDER=ollama: Uses openai.OpenAI with Ollama base_url.
    - If LLM_PROVIDER=groq: Uses Groq client with GROQ_API_KEY.
    """
    global _client, _current_provider
    provider = get_llm_provider()

    if _client is not None and _current_provider == provider:
        return _client, provider

    if provider == "groq":
        from groq import Groq
        api_key = os.getenv("GROQ_API_KEY", "")
        _client = Groq(api_key=api_key)
        _current_provider = "groq"
        logger.info("[LLM] Initialized Groq client.")
    else:
        # Default to Ollama via OpenAI-compatible endpoint
        from openai import OpenAI
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
        # Ollama local endpoint does not require a real API key, but OpenAI client needs non-empty string
        _client = OpenAI(base_url=base_url, api_key="ollama")
        _current_provider = "ollama"
        logger.info(f"[LLM] Initialized Ollama client with base_url={base_url}")

    return _client, provider

def get_llm_model_name() -> str:
    """Returns the model name depending on active provider."""
    provider = get_llm_provider()
    if provider == "groq":
        return os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
    else:
        return os.getenv("OLLAMA_MODEL", "qwen2.5:3b")

def generate_chat_completion(messages: List[Dict[str, str]], temperature: float = 0.1, max_tokens: Optional[int] = None) -> str:
    """
    Unified function to generate chat completions using either Ollama or Groq,
    with automatic rate-limit (HTTP 429) backoff and retries.
    """
    import time
    client, provider = get_llm_client()
    model = get_llm_model_name()

    kwargs: Dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": temperature
    }
    if max_tokens:
        kwargs["max_tokens"] = max_tokens

    max_retries = 5
    backoff = 3.0

    for attempt in range(1, max_retries + 1):
        try:
            logger.debug(f"[LLM] Calling {provider} (model={model}, attempt={attempt})...")
            response = client.chat.completions.create(**kwargs)
            return response.choices[0].message.content or ""
        except Exception as e:
            err_msg = str(e).lower()
            if "429" in err_msg or "rate limit" in err_msg or "too many requests" in err_msg:
                logger.warning(f"[LLM] Rate limit hit on {provider}. Waiting {backoff:.1f}s before retry (attempt {attempt}/{max_retries})...")
                time.sleep(backoff)
                backoff *= 2.0
            elif attempt == max_retries:
                logger.error(f"[LLM] Error calling {provider}: {e}")
                raise
            else:
                logger.warning(f"[LLM] Transient error: {e}. Retrying in 2s...")
                time.sleep(2.0)
    return ""
