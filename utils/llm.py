from typing import Optional, Tuple

from openai import OpenAI

from configs.settings import get_settings


def get_client_and_model(model: Optional[str]) -> Tuple[OpenAI, str, str]:
    settings = get_settings()
    provider = settings.llm_provider

    if provider == "openai":
        api_key = settings.openai_api_key
        base_url = settings.openai_base_url
    elif provider == "openrouter":
        api_key = settings.openrouter_api_key
        base_url = settings.openrouter_base_url
    elif provider == "groq":
        api_key = settings.groq_api_key
        base_url = settings.groq_base_url
    elif provider == "deepseek":
        api_key = settings.deepseek_api_key
        base_url = settings.deepseek_base_url
    else:
        raise RuntimeError(f"Unsupported LLM_PROVIDER: {provider}")

    if not api_key:
        key_name = {
            "openai": "OPENAI_API_KEY",
            "openrouter": "OPENROUTER_API_KEY",
            "groq": "GROQ_API_KEY",
            "deepseek": "DEEPSEEK_API_KEY",
        }[provider]
        raise RuntimeError(f"{key_name} is required for provider '{provider}'.")

    client = OpenAI(api_key=api_key, base_url=base_url)
    return client, model or "", provider
