# Medicare LLM Evaluation System

A research tool for assessing the quality of AI responses to Medicare-related questions. This system programmatically tests multiple large language models (LLMs) against a standardized set of questions and scores their accuracy using semantic similarity.

## Overview

This tool evaluates how well different LLMs answer Medicare questions by:
- Querying multiple AI models with standardized Medicare questions
- Computing semantic similarity scores between responses and ground truth answers
- Storing all results in a SQLite database for analysis
- Providing a web interface for running tests and viewing results

**Version**: 1.0 (MVP)

## Quick Start

### Prerequisites
- Python 3.8 or higher
- OpenRouter API key ([get one here](https://openrouter.ai/keys))

### Installation

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure API key**:
   ```bash
   cp .env.example .env
   # Edit .env and add your OPENROUTER_API_KEY
   ```

3. **Start the backend**:
   ```bash
   python -m backend.app
   ```

4. **Start the frontend** (in a new terminal):
   ```bash
   python3 -m http.server 8080
   ```

5. **Open in browser**: http://localhost:8080

See [SETUP.md](SETUP.md) for detailed instructions and troubleshooting.

## Features

### Models Tested
- **GPT-4** (OpenAI)
- **Claude Sonnet 4.5** (Anthropic)
- **Gemini 2.0 Flash** (Google)
- **Grok 2** (xAI)
- **DeepSeek Chat** (DeepSeek)

### Question Set
20 Medicare questions covering:
- Basic eligibility (5 questions)
- Costs and premiums (5 questions)
- Coverage details (5 questions)
- Enrollment periods (5 questions)

### Scoring Methodology
Uses **embedding-based semantic similarity**:
- Computes embeddings for ground truth and model responses
- Calculates cosine similarity between embeddings
- Maps similarity to 1-10 score (10 = near identical, 1 = very different)
- Provides aggregate scores per model, per question, and overall

### Interface Features
- Model selection with checkboxes
- Real-time test progress tracking
- Detailed results viewer with score grids
- Individual response comparisons
- Execution logs for debugging
- Test run history

## Architecture

```
Frontend (Browser)
    ↓ HTTP requests
FastAPI Backend (Port 8000)
    ↓ Query models
OpenRouter API → LLMs (GPT-4, Claude, etc.)
    ↓ Compute similarity
OpenAI Embeddings API
    ↓ Store results
SQLite Database (data/evaluation_results.db)
```

### Backend Components
- `backend/app.py` - FastAPI server with REST endpoints
- `backend/test_runner.py` - Test orchestration and execution
- `backend/scorer.py` - Semantic similarity scoring
- `backend/database.py` - SQLite database manager
- `backend/openrouter.py` - LLM API client
- `backend/config.py` - Model configuration

### Frontend
- `index.html` - Web interface for model selection and results
- Single-page application using vanilla JavaScript

### Data Storage
- `data/questions_v1.json` - Ground truth questions and answers
- `data/evaluation_results.db` - SQLite database (auto-created)

## API Endpoints

- `GET /api/models` - List available models
- `GET /api/questions` - Get question set
- `POST /api/test-runs` - Start a new test run
- `GET /api/test-runs/{run_id}` - Get test run details
- `GET /api/test-runs/{run_id}/logs` - Get test run logs
- `GET /api/test-runs` - List all test runs

## Documentation

- [PRD.md](PRD.md) - Product requirements and specifications
- [SETUP.md](SETUP.md) - Detailed setup and usage instructions
- [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) - Technical implementation details
- [overview.md](overview.md) - Project motivation and approach

## Usage

1. **Select models**: Check the boxes next to models you want to test
2. **Run test**: Click "Run Test" to start evaluation
3. **Monitor progress**: Status section shows test progress in real-time
4. **View results**: See aggregate scores, score grids, and detailed responses
5. **Check logs**: View execution logs for debugging
6. **Review history**: Access past test runs with "Load Test History"

## Extensibility

The system is designed to be easily extended:
- **Add questions**: Update `data/questions_v1.json`
- **Add models**: Update `backend/config.py`
- **Add scoring methods**: Extend `backend/scorer.py`

## Out of Scope for MVP 1.0

The following are planned for future versions:
- Custom model settings (temperature, max_tokens)
- Multiple scoring methods
- System prompt optimization
- Historical comparisons
- Cost tracking
- CSV/PDF export
- Statistical significance testing

See [PRD.md](PRD.md) for complete list of future features.

## Notes

- This tool is for research and evaluation purposes
- All test results are persisted and can be reviewed later
- Model responses reflect "out of the box" performance with default settings
- Scoring is based on semantic similarity, not exact string matching

## Troubleshooting

See [SETUP.md](SETUP.md) for common issues and solutions.

## License

This is a research prototype for evaluating AI responses to Medicare questions.
