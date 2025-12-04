"""Configuration for Medicare LLM Evaluation System."""

import os
from dotenv import load_dotenv

load_dotenv()

# OpenRouter API key
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# OpenRouter API endpoint
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Models available for testing (as per PRD v1.0)
AVAILABLE_MODELS = {
    "GPT-4": "openai/gpt-4o",
    "Claude": "anthropic/claude-sonnet-4.5",
    "Gemini": "google/gemini-2.0-flash-exp:free",
    "Grok": "x-ai/grok-2-vision-1212",
    "DeepSeek": "deepseek/deepseek-chat",
}

# Embedding model for scoring
EMBEDDING_MODEL = "openai/text-embedding-3-small"

# Data paths
QUESTIONS_PATH = "data/questions_v1.json"
DATABASE_PATH = "data/evaluation_results.db"
