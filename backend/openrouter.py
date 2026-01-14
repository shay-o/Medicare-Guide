"""OpenRouter API client for making LLM requests."""

import httpx
import logging
from typing import List, Dict, Any, Optional
from .config import OPENROUTER_API_KEY, OPENROUTER_API_URL

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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

    # Validate API key exists
    if not OPENROUTER_API_KEY:
        logger.error("❌ OPENROUTER_API_KEY not found in environment variables!")
        logger.error("   Make sure your .env file has: OPENROUTER_API_KEY=your_key_here")
        return None

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            logger.info(f"🔄 Querying model: {model}")
            response = await client.post(
                OPENROUTER_API_URL,
                headers=headers,
                json=payload
            )

            # Log response status
            logger.info(f"📡 Response status: {response.status_code}")

            # Handle specific HTTP errors with helpful messages
            if response.status_code == 401:
                logger.error("❌ Authentication failed (401)")
                logger.error("   Your API key is invalid or expired")
                logger.error("   Get a new key: https://openrouter.ai/keys")
                return None
            elif response.status_code == 402:
                logger.error("❌ Payment required (402)")
                logger.error("   Your account needs credits")
                logger.error("   Add credits: https://openrouter.ai/credits")
                return None
            elif response.status_code == 429:
                logger.error("❌ Rate limit exceeded (429)")
                logger.error("   Too many requests. Wait and try again.")
                return None

            response.raise_for_status()

            data = response.json()
            message = data['choices'][0]['message']

            logger.info(f"✅ Successfully got response from {model}")

            return {
                'content': message.get('content'),
                'model': model,
                'usage': data.get('usage', {}),
            }

    except httpx.TimeoutException:
        logger.error(f"⏱️  Timeout querying model {model} (>{timeout}s)")
        return None
    except httpx.HTTPStatusError as e:
        logger.error(f"❌ HTTP error querying {model}: {e.response.status_code}")
        logger.error(f"   Response: {e.response.text}")
        return None
    except Exception as e:
        logger.error(f"❌ Unexpected error querying model {model}: {type(e).__name__}: {e}")
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

    if not OPENROUTER_API_KEY:
        logger.error("❌ OPENROUTER_API_KEY not found in environment variables!")
        return None

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            logger.info(f"🔄 Getting embedding with model: {model}")
            response = await client.post(
                "https://openrouter.ai/api/v1/embeddings",
                headers=headers,
                json=payload
            )

            if response.status_code == 401:
                logger.error("❌ Authentication failed getting embedding")
                logger.error("   Check your API key: https://openrouter.ai/keys")
                return None

            response.raise_for_status()

            data = response.json()
            logger.info("✅ Successfully got embedding")
            return data['data'][0]['embedding']

    except httpx.HTTPStatusError as e:
        logger.error(f"❌ HTTP error getting embedding: {e.response.status_code}")
        logger.error(f"   Response: {e.response.text}")
        return None
    except Exception as e:
        logger.error(f"❌ Error getting embedding: {type(e).__name__}: {e}")
        return None
