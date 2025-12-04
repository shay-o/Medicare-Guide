"""Scoring system using embedding-based semantic similarity."""

import numpy as np
from datetime import datetime
from typing import Dict, Any
from .openrouter import get_embedding
from .config import EMBEDDING_MODEL


async def cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
    """Calculate cosine similarity between two vectors."""
    v1 = np.array(vec1)
    v2 = np.array(vec2)

    dot_product = np.dot(v1, v2)
    norm_v1 = np.linalg.norm(v1)
    norm_v2 = np.linalg.norm(v2)

    if norm_v1 == 0 or norm_v2 == 0:
        return 0.0

    return float(dot_product / (norm_v1 * norm_v2))


def similarity_to_score(similarity: float) -> int:
    """
    Map cosine similarity to 1-10 score based on PRD specification.

    Mapping:
    - >= 0.95: Score = 10 (Near identical)
    - >= 0.90: Score = 9
    - >= 0.85: Score = 8
    - >= 0.80: Score = 7
    - >= 0.75: Score = 6
    - >= 0.70: Score = 5
    - >= 0.65: Score = 4
    - >= 0.60: Score = 3
    - >= 0.55: Score = 2
    - < 0.55: Score = 1
    """
    if similarity >= 0.95:
        return 10
    elif similarity >= 0.90:
        return 9
    elif similarity >= 0.85:
        return 8
    elif similarity >= 0.80:
        return 7
    elif similarity >= 0.75:
        return 6
    elif similarity >= 0.70:
        return 5
    elif similarity >= 0.65:
        return 4
    elif similarity >= 0.60:
        return 3
    elif similarity >= 0.55:
        return 2
    else:
        return 1


async def score_response(ground_truth: str, model_response: str) -> Dict[str, Any]:
    """
    Score a model response against ground truth using embedding similarity.

    Args:
        ground_truth: The correct answer
        model_response: The LLM's actual response

    Returns:
        Dict with score and metadata
    """
    # Get embeddings for both texts
    ground_truth_embedding = await get_embedding(ground_truth, EMBEDDING_MODEL)
    response_embedding = await get_embedding(model_response, EMBEDDING_MODEL)

    if ground_truth_embedding is None or response_embedding is None:
        # If embeddings fail, return error
        return {
            "score": 0,
            "metadata": {
                "error": "Failed to generate embeddings",
                "embedding_model": EMBEDDING_MODEL,
                "scored_at": datetime.utcnow().isoformat()
            }
        }

    # Calculate similarity
    similarity = await cosine_similarity(ground_truth_embedding, response_embedding)

    # Map to score
    score = similarity_to_score(similarity)

    # Build metadata
    metadata = {
        "cosine_similarity": float(similarity),
        "embedding_model": EMBEDDING_MODEL,
        "scored_at": datetime.utcnow().isoformat()
    }

    return {
        "score": score,
        "metadata": metadata
    }
