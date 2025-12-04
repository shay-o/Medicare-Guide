# Setup Guide

## Prerequisites

- Python 3.8 or higher
- OpenRouter API key (get one at https://openrouter.ai/keys)

## Installation

1. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables**:
   ```bash
   cp .env.example .env
   ```
   Then edit `.env` and add your OpenRouter API key.

3. **Verify data directory exists**:
   The `data/` directory should already contain `questions_v1.json`. The database will be created automatically on first run.

## Running the System

### 1. Start the Backend Server

```bash
python -m backend.app
```

This starts the FastAPI server on `http://localhost:8000`.

You can verify it's running by visiting http://localhost:8000 in your browser.

### 2. Start the Frontend Server

In a new terminal, start a simple HTTP server for the frontend:

```bash
python3 -m http.server 8080
```

Then open http://localhost:8080 in your browser.

## Using the System

1. **Select Models**: Check the boxes next to the models you want to test
2. **Run Test**: Click "Run Test" to start the evaluation
3. **Monitor Progress**: The status section will show test progress
4. **View Results**: Once complete, you'll see:
   - Aggregate scores (overall, per-model, per-question)
   - Score grid showing individual question × model scores
   - Detailed responses with ground truth comparisons
   - Test execution logs
5. **View History**: Click "Load Test History" to see past test runs

## Troubleshooting

### "Failed to load models" error
- Make sure the backend server is running on port 8000
- Check that your `.env` file has a valid OPENROUTER_API_KEY

### CORS errors
- Make sure you're accessing the frontend via http://localhost:8080 (or another local server)
- Don't open index.html directly as a file

### Test fails immediately
- Check backend logs for error messages
- Verify your OpenRouter API key has sufficient credits
- Ensure all required models are available on OpenRouter

## API Endpoints

The backend exposes these endpoints:

- `GET /api/models` - List available models
- `GET /api/questions` - Get question set
- `POST /api/test-runs` - Start a new test run
- `GET /api/test-runs/{run_id}` - Get test run details
- `GET /api/test-runs/{run_id}/logs` - Get test run logs
- `GET /api/test-runs` - List all test runs

## Data Storage

- Questions: `data/questions_v1.json`
- Database: `data/evaluation_results.db` (SQLite)

All test results are persisted in the database and can be viewed later.
