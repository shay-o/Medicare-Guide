"""OpenRouter API client for making LLM requests."""

import httpx
from typing import List, Dict, Any, Optional
from .config import OPENROUTER_API_KEY, OPENROUTER_API_URL


async def query_model(
    model: str,
    messages: List[Dict[str, str]],
    temperature: float = 0.7,
    max_tokens: int = 1000,
    timeout: float = 120.0
) -> Optional[Dict[str, Any]]:
    """
    Query a single model via OpenRouter API.

    Args:
        model: OpenRouter model identifier (e.g., "anthropic/claude-sonnet-4.5")
        messages: List of message dicts with 'role' and 'content'
        temperature: Sampling temperature (0.0-1.0)
        max_tokens: Maximum tokens in response
        timeout: Request timeout in seconds

    Returns:
        Response dict with 'content' and metadata, or None if failed
    """
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                OPENROUTER_API_URL,
                headers=headers,
                json=payload
            )
            response.raise_for_status()

            data = response.json()
            message = data['choices'][0]['message']

            return {
                'content': message.get('content'),
                'model': model,
                'usage': data.get('usage', {}),
            }

    except Exception as e:
        print(f"Error querying model {model}: {e}")
        return None


async def query_models_parallel(
    models: List[str],
    messages: List[Dict[str, str]],
    temperature: float = 0.7,
    max_tokens: int = 1000,
) -> Dict[str, Optional[Dict[str, Any]]]:
    """
    Query multiple models in parallel for comparison.

    Args:
        models: List of OpenRouter model identifiers
        messages: List of message dicts to send to each model
        temperature: Sampling temperature
        max_tokens: Maximum tokens in response

    Returns:
        Dict mapping model identifier to response dict (or None if failed)
    """
    import asyncio

    # Create tasks for all models
    tasks = [
        query_model(model, messages, temperature, max_tokens)
        for model in models
    ]

    # Wait for all to complete
    responses = await asyncio.gather(*tasks)

    # Map models to their responses
    return {model: response for model, response in zip(models, responses)}


async def get_embedding(text: str, model: str) -> Optional[List[float]]:
    """
    Get embedding vector for text via OpenRouter.

    Note: OpenRouter supports OpenAI embedding models.
    For better performance/cost, consider calling OpenAI directly.

    Args:
        text: Text to embed
        model: Embedding model identifier

    Returns:
        Embedding vector (list of floats) or None if failed
    """
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": model,
        "input": text,
    }

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/embeddings",
                headers=headers,
                json=payload
            )
            response.raise_for_status()

            data = response.json()
            return data['data'][0]['embedding']

    except Exception as e:
        print(f"Error getting embedding: {e}")
        return None
