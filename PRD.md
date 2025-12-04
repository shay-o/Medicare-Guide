# Overview

This document represents the specification of how this tool should work. The code in this repo will be based on this document. 
Any user-facing changes such as functionality or UI, will be start with changes in this doc which will then result in changes in code.  

The goal of this tool is to assess the quality of information provided by various service about Medicare to end users. This represents the initial MVP version of this tool.  

_Motivation_: AI has the potential to improve people's ability to access Medicare services by, among other things, improving their understanding of what is available and how to access it.   

This project is intended to explore how we can assess the quality of AI advice in order to understand whether is useful and to understand how it can be improved.

# Version
1.0 (Draft)

# Development Process
This PRD follows a specification-first approach:
1. Changes to functionality or UI start with updates to this document
2. Code is then updated to match the PRD
3. When implementation reveals PRD gaps or issues, the PRD should be updated immediately before continuing
4. Sections marked "TBD" indicate areas needing further specification

# Approach
For this MVP version we will create a tool that progammatically captures responses from LLM-based tools, assesses these responses based on a set of known correct answers, and provides reporting on the results.

# Plan for MVP 1.0
- Develop an end-to-end of a measurement system for assessing LLM based responses to a standard set of questions. Goal it is to build out a scaffolding for an end-to-end system.
- Create a ground truth set of 20 questions and answers. 
- Programmatically hit 3 LLMs with these test questions and capture the responses.
- Score the results using a semantic comparison.
- Report on the results
- This should be extensible to add more questions, different assessment menthodologies and different sources of information (ie other LLMS or different inputs for those LLMs)

# Functionality for MVP 1.0

## Models
The following models will be available for testing (accessed via OpenRouter API):
- **GPT-4**: `openai/gpt-4o` (latest GPT-4 model)
- **Claude**: `anthropic/claude-sonnet-4.5` (Claude Sonnet 4.5)
- **Gemini**: `google/gemini-2.0-flash-exp` (Gemini 2.0 Flash)
- **Grok**: `x-ai/grok-2-vision-1212` (Grok 2)
- **DeepSeek**: `deepseek/deepseek-chat` (DeepSeek Chat)

**Model Settings for MVP 1.0**:
- **No custom parameters**: Models will be tested with their default settings (temperature, max_tokens, etc.)
- **No system prompts**: Questions will be sent directly without role-setting prompts
- **Rationale**: This evaluates the "out of the box" experience that typical users would encounter

**Future Testing** (post-MVP 1.0):
- Comparative tests with different temperature settings
- Impact of system prompts on accuracy
- Effect of max_tokens constraints
- Model settings are themselves part of what will be evaluated in future versions

## Interface
- The interface will allow users to run a test of the question set against a selection of LLMs
- Users can select one, several, or all models using checkboxes
- A "Run Test" button initiates the evaluation
- Status indicator shows:
  - "Running" - with progress (e.g., "Testing 3 of 5 models...")
  - "Completed Successfully" - with timestamp
  - "Error" - with error message
- A log viewer displays detailed execution information:
  - Timestamp for each action
  - Model being queried
  - Question being asked
  - Response received
  - Any errors or warnings
- Results viewer displays:
  - Individual scores (question × model grid)
  - Aggregate scores per model (average across all questions)
  - Aggregate scores per question (average across all models)
  - Overall test run average
  - Ability to view full question/answer pairs

## Back End

### Data Storage
**Storage Format**: SQLite database (`data/evaluation_results.db`)
- Simple, portable, no server setup required
- Suitable for research/prototype scale
- Can be migrated to PostgreSQL later if needed

**Schema**:

**test_runs** table:
- `run_id` (TEXT, PRIMARY KEY) - UUID v4
- `created_at` (TIMESTAMP) - ISO 8601 format
- `status` (TEXT) - "running", "completed", "failed"
- `models_tested` (TEXT) - JSON array of model IDs
- `question_set_version` (TEXT) - e.g., "1.0"
- `error_message` (TEXT, nullable) - Error details if failed

**responses** table:
- `response_id` (TEXT, PRIMARY KEY) - UUID v4
- `run_id` (TEXT, FOREIGN KEY) - Links to test_runs
- `question_id` (TEXT) - Identifier for the question (e.g., "Q001")
- `model_id` (TEXT) - OpenRouter model identifier
- `model_settings` (TEXT) - JSON with actual settings used (temperature, max_tokens, etc.)
- `question_text` (TEXT) - Full question text
- `ground_truth` (TEXT) - Expected correct answer
- `model_response` (TEXT) - LLM's actual response
- `response_time_ms` (INTEGER) - Time to get response
- `timestamp` (TIMESTAMP) - When response was received
- `score` (REAL) - Computed score (1-10)
- `scoring_metadata` (TEXT) - JSON with scoring details

**logs** table:
- `log_id` (INTEGER, PRIMARY KEY AUTOINCREMENT)
- `run_id` (TEXT, FOREIGN KEY) - Links to test_runs
- `timestamp` (TIMESTAMP) - ISO 8601 format
- `level` (TEXT) - "INFO", "WARNING", "ERROR"
- `message` (TEXT) - Log message
- `context` (TEXT) - JSON with additional context (model, question, etc.)

### Ground Truth Questions
**Storage**: `data/questions_v1.json`

Format:
```json
{
  "version": "1.0",
  "questions": [
    {
      "id": "Q001",
      "question": "What is the standard Part B premium for 2024?",
      "ground_truth": "The standard Part B premium for 2024 is $174.70 per month.",
      "category": "costs",
      "difficulty": "easy"
    }
  ]
}
```

Initial set: 20 questions covering:
- Basic eligibility (5 questions)
- Costs and premiums (5 questions)
- Coverage details (5 questions)
- Enrollment periods (5 questions)

### Scoring Methodology

**Method**: Embedding-based semantic similarity
- Use OpenAI's `text-embedding-3-small` model via OpenRouter
- Compute embeddings for both ground truth and model response
- Calculate cosine similarity between embeddings
- Map similarity to 1-10 score

**Similarity to Score Mapping**:
- Cosine similarity ≥ 0.95: Score = 10 (Near identical)
- Cosine similarity ≥ 0.90: Score = 9
- Cosine similarity ≥ 0.85: Score = 8
- Cosine similarity ≥ 0.80: Score = 7
- Cosine similarity ≥ 0.75: Score = 6
- Cosine similarity ≥ 0.70: Score = 5
- Cosine similarity ≥ 0.65: Score = 4
- Cosine similarity ≥ 0.60: Score = 3
- Cosine similarity ≥ 0.55: Score = 2
- Cosine similarity < 0.55: Score = 1

**Rationale**: Semantic embeddings capture meaning better than exact string matching, allowing for variations in phrasing while penalizing incorrect information.

**Stored Metadata** (in `scoring_metadata` JSON):
```json
{
  "cosine_similarity": 0.87,
  "embedding_model": "openai/text-embedding-3-small",
  "scored_at": "2024-03-15T10:30:00Z"
}
```

**Aggregate Calculations**:
- Per-model average: Mean of all scores for that model across all questions for this test run
- Per-question average: Mean of all scores for that question across all models for this test run
- Test run average: Mean of all scores in this test run (all models × all questions)

## Technical Architecture

**Frontend**: Single-page application
- HTML/CSS/JavaScript (no framework required for MVP)
- Uses Tailwind CSS for styling
- Communicates with backend via REST API

**Backend**: Python-based API server
- FastAPI or Flask for REST endpoints
- Async request handling for parallel model queries
- SQLite for data persistence
- OpenRouter client for LLM access

**Key Components**:
- Test runner: Orchestrates test execution, queries models in parallel
- Scorer: Computes embeddings and similarity scores
- Database manager: Handles all data persistence
- Logger: Writes structured logs to database

**API Endpoints** (preliminary):
- `POST /api/test-runs` - Start a new test run
- `GET /api/test-runs/{run_id}` - Get test run status and results
- `GET /api/test-runs/{run_id}/logs` - Get logs for a test run
- `GET /api/test-runs` - List all test runs (with pagination)
- `GET /api/questions` - Get current question set

# Acceptance Criteria

MVP 1.0 is considered complete when:

**Core Functionality**:
- ✓ User can select 1 or more models from the 5 available models
- ✓ User can initiate a test run with selected models
- ✓ System queries all selected models with all 20 questions
- ✓ All responses are stored in the database with correct schema
- ✓ All responses are scored using embedding similarity
- ✓ Aggregate scores are calculated correctly

**Interface**:
- ✓ Status indicator updates correctly (running → completed/failed)
- ✓ Progress shows which model is being tested
- ✓ Log viewer displays all test actions with timestamps
- ✓ Results viewer shows individual scores in a grid format
- ✓ Results viewer shows aggregate scores (per-model, per-question, overall)
- ✓ User can view full question text, ground truth, and model response

**Data & Reliability**:
- ✓ Database schema matches specification
- ✓ Test runs can be retrieved after completion
- ✓ Errors are logged with sufficient detail for debugging
- ✓ System handles API failures gracefully (retry logic, timeout handling)

**Extensibility**:
- ✓ Adding new questions requires only updating JSON file
- ✓ Adding new models requires only updating config file
- ✓ Code is structured to support future scoring methods

# Out of Scope for MVP 1.0

The following features are explicitly NOT included in MVP 1.0:

**Features for Future Versions**:
- Custom question sets (only v1.0 question set supported)
- Multiple scoring methods (only embedding similarity in MVP)
- Testing with custom model settings (temperature, max_tokens, etc.)
- System prompt optimization and A/B testing
- Comparison across historical test runs
- Exporting results to CSV/PDF
- Cost tracking for API usage
- Real-time streaming of responses
- Statistical significance testing
- User authentication/multi-user support
- Question difficulty weighting
- Custom similarity thresholds per question

**Infrastructure**:
- Production deployment configuration
- Automated testing suite
- CI/CD pipeline
- Database migrations
- Rate limiting
- Caching layer

# Implementation Notes

This section captures learnings and decisions made during implementation:

_(To be filled in as implementation proceeds)_

