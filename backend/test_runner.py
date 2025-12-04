"""Test runner for evaluating LLMs against Medicare questions."""

import asyncio
import json
import time
from typing import List, Dict, Any
from pathlib import Path
from .database import DatabaseManager
from .openrouter import query_model
from .scorer import score_response


async def load_questions(questions_file: str = "data/questions_v1.json") -> Dict[str, Any]:
    """Load questions from JSON file."""
    with open(questions_file, 'r') as f:
        return json.load(f)


async def run_test(
    models: List[str],
    db: DatabaseManager,
    quick_test: bool = False,
    questions_file: str = "data/questions_v1.json"
) -> str:
    """
    Run evaluation test for selected models.

    Args:
        models: List of model IDs to test
        db: Database manager instance
        quick_test: If True, only run first question (for testing)
        questions_file: Path to questions JSON file

    Returns:
        run_id of the test run
    """
    # Load questions
    questions_data = await load_questions(questions_file)
    questions = questions_data["questions"]
    question_set_version = questions_data["version"]

    # If quick test, only use first question
    if quick_test:
        questions = questions[:1]

    # Create test run
    run_id = db.create_test_run(models, question_set_version)
    db.log(run_id, "INFO", f"Starting test run with {len(models)} models and {len(questions)} questions")

    try:
        # Process each model
        for model_idx, model_id in enumerate(models):
            db.log(run_id, "INFO", f"Testing model {model_idx + 1} of {len(models)}: {model_id}")

            # Process each question for this model
            for question_idx, question in enumerate(questions):
                question_id = question["id"]
                question_text = question["question"]
                ground_truth = question["ground_truth"]

                db.log(
                    run_id,
                    "INFO",
                    f"Querying {model_id} with question {question_id}",
                    {"model": model_id, "question_id": question_id}
                )

                # Query the model
                start_time = time.time()
                try:
                    # Send question directly without system prompt (as per PRD)
                    messages = [{"role": "user", "content": question_text}]
                    response = await query_model(model_id, messages)

                    if response is None:
                        raise Exception("Model returned None response")

                    response_time_ms = int((time.time() - start_time) * 1000)
                    model_response = response["content"]
                    model_settings = {
                        "usage": response.get("usage", {})
                    }

                    db.log(
                        run_id,
                        "INFO",
                        f"Received response from {model_id} for {question_id} ({response_time_ms}ms)",
                        {"model": model_id, "question_id": question_id, "response_time_ms": response_time_ms}
                    )

                    # Save response without score first
                    response_id = db.save_response(
                        run_id=run_id,
                        question_id=question_id,
                        model_id=model_id,
                        model_settings=model_settings,
                        question_text=question_text,
                        ground_truth=ground_truth,
                        model_response=model_response,
                        response_time_ms=response_time_ms
                    )

                    # Score the response
                    db.log(run_id, "INFO", f"Scoring response {response_id}")
                    score_result = await score_response(ground_truth, model_response)

                    # Update with score
                    db.update_response_score(
                        response_id=response_id,
                        score=score_result["score"],
                        scoring_metadata=score_result["metadata"]
                    )

                    db.log(
                        run_id,
                        "INFO",
                        f"Scored response {response_id}: {score_result['score']}/10",
                        {"response_id": response_id, "score": score_result["score"]}
                    )

                except Exception as e:
                    error_msg = f"Error querying {model_id} for question {question_id}: {str(e)}"
                    db.log(run_id, "ERROR", error_msg, {"model": model_id, "question_id": question_id, "error": str(e)})

                    # Save error response
                    response_time_ms = int((time.time() - start_time) * 1000)
                    db.save_response(
                        run_id=run_id,
                        question_id=question_id,
                        model_id=model_id,
                        model_settings={},
                        question_text=question_text,
                        ground_truth=ground_truth,
                        model_response=f"ERROR: {str(e)}",
                        response_time_ms=response_time_ms,
                        score=0,
                        scoring_metadata={"error": str(e)}
                    )

        # Mark test as completed
        db.update_test_run_status(run_id, "completed")
        db.log(run_id, "INFO", "Test run completed successfully")

    except Exception as e:
        # Mark test as failed
        error_message = str(e)
        db.update_test_run_status(run_id, "failed", error_message)
        db.log(run_id, "ERROR", f"Test run failed: {error_message}")
        raise

    return run_id


async def run_test_background(models: List[str], db: DatabaseManager) -> str:
    """
    Run test in background and return run_id immediately.

    This allows the API to return while the test runs.
    """
    run_id = await run_test(models, db)
    return run_id
