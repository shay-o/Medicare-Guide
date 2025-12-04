"""Database manager for Medicare LLM evaluation system."""

import sqlite3
import json
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path


class DatabaseManager:
    """Manages SQLite database operations for test runs, responses, and logs."""

    def __init__(self, db_path: str = "data/evaluation_results.db"):
        """Initialize database connection and create tables if needed."""
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._create_tables()

    def _create_tables(self):
        """Create database tables if they don't exist."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # test_runs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS test_runs (
                    run_id TEXT PRIMARY KEY,
                    created_at TIMESTAMP NOT NULL,
                    status TEXT NOT NULL,
                    models_tested TEXT NOT NULL,
                    question_set_version TEXT NOT NULL,
                    error_message TEXT
                )
            """)

            # responses table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS responses (
                    response_id TEXT PRIMARY KEY,
                    run_id TEXT NOT NULL,
                    question_id TEXT NOT NULL,
                    model_id TEXT NOT NULL,
                    model_settings TEXT,
                    question_text TEXT NOT NULL,
                    ground_truth TEXT NOT NULL,
                    model_response TEXT NOT NULL,
                    response_time_ms INTEGER NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    score REAL,
                    scoring_metadata TEXT,
                    FOREIGN KEY (run_id) REFERENCES test_runs (run_id)
                )
            """)

            # logs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS logs (
                    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    level TEXT NOT NULL,
                    message TEXT NOT NULL,
                    context TEXT,
                    FOREIGN KEY (run_id) REFERENCES test_runs (run_id)
                )
            """)

            conn.commit()

    def create_test_run(self, models: List[str], question_set_version: str = "1.0") -> str:
        """Create a new test run and return its ID."""
        run_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO test_runs (run_id, created_at, status, models_tested, question_set_version)
                VALUES (?, ?, ?, ?, ?)
            """, (run_id, now, "running", json.dumps(models), question_set_version))
            conn.commit()

        return run_id

    def update_test_run_status(self, run_id: str, status: str, error_message: Optional[str] = None):
        """Update the status of a test run."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE test_runs
                SET status = ?, error_message = ?
                WHERE run_id = ?
            """, (status, error_message, run_id))
            conn.commit()

    def save_response(
        self,
        run_id: str,
        question_id: str,
        model_id: str,
        model_settings: Dict[str, Any],
        question_text: str,
        ground_truth: str,
        model_response: str,
        response_time_ms: int,
        score: Optional[float] = None,
        scoring_metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Save a model response to the database."""
        response_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO responses (
                    response_id, run_id, question_id, model_id, model_settings,
                    question_text, ground_truth, model_response, response_time_ms,
                    timestamp, score, scoring_metadata
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                response_id, run_id, question_id, model_id, json.dumps(model_settings),
                question_text, ground_truth, model_response, response_time_ms,
                now, score, json.dumps(scoring_metadata) if scoring_metadata else None
            ))
            conn.commit()

        return response_id

    def update_response_score(
        self,
        response_id: str,
        score: float,
        scoring_metadata: Dict[str, Any]
    ):
        """Update the score for a response."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE responses
                SET score = ?, scoring_metadata = ?
                WHERE response_id = ?
            """, (score, json.dumps(scoring_metadata), response_id))
            conn.commit()

    def log(
        self,
        run_id: str,
        level: str,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ):
        """Write a log entry."""
        now = datetime.utcnow().isoformat()

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO logs (run_id, timestamp, level, message, context)
                VALUES (?, ?, ?, ?, ?)
            """, (run_id, now, level, message, json.dumps(context) if context else None))
            conn.commit()

    def get_test_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        """Get test run information."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM test_runs WHERE run_id = ?", (run_id,))
            row = cursor.fetchone()

            if row:
                return {
                    "run_id": row["run_id"],
                    "created_at": row["created_at"],
                    "status": row["status"],
                    "models_tested": json.loads(row["models_tested"]),
                    "question_set_version": row["question_set_version"],
                    "error_message": row["error_message"]
                }
            return None

    def get_responses(self, run_id: str) -> List[Dict[str, Any]]:
        """Get all responses for a test run."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM responses WHERE run_id = ? ORDER BY question_id, model_id", (run_id,))
            rows = cursor.fetchall()

            return [
                {
                    "response_id": row["response_id"],
                    "run_id": row["run_id"],
                    "question_id": row["question_id"],
                    "model_id": row["model_id"],
                    "model_settings": json.loads(row["model_settings"]) if row["model_settings"] else {},
                    "question_text": row["question_text"],
                    "ground_truth": row["ground_truth"],
                    "model_response": row["model_response"],
                    "response_time_ms": row["response_time_ms"],
                    "timestamp": row["timestamp"],
                    "score": row["score"],
                    "scoring_metadata": json.loads(row["scoring_metadata"]) if row["scoring_metadata"] else {}
                }
                for row in rows
            ]

    def get_logs(self, run_id: str) -> List[Dict[str, Any]]:
        """Get all logs for a test run."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM logs WHERE run_id = ? ORDER BY timestamp", (run_id,))
            rows = cursor.fetchall()

            return [
                {
                    "log_id": row["log_id"],
                    "run_id": row["run_id"],
                    "timestamp": row["timestamp"],
                    "level": row["level"],
                    "message": row["message"],
                    "context": json.loads(row["context"]) if row["context"] else {}
                }
                for row in rows
            ]

    def get_all_test_runs(self, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """Get all test runs with pagination."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM test_runs
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            """, (limit, offset))
            rows = cursor.fetchall()

            return [
                {
                    "run_id": row["run_id"],
                    "created_at": row["created_at"],
                    "status": row["status"],
                    "models_tested": json.loads(row["models_tested"]),
                    "question_set_version": row["question_set_version"],
                    "error_message": row["error_message"]
                }
                for row in rows
            ]

    def calculate_aggregates(self, run_id: str) -> Dict[str, Any]:
        """Calculate aggregate scores for a test run."""
        responses = self.get_responses(run_id)

        if not responses:
            return {}

        # Overall average
        scores = [r["score"] for r in responses if r["score"] is not None]
        overall_avg = sum(scores) / len(scores) if scores else 0

        # Per-model averages
        model_scores: Dict[str, List[float]] = {}
        for r in responses:
            if r["score"] is not None:
                if r["model_id"] not in model_scores:
                    model_scores[r["model_id"]] = []
                model_scores[r["model_id"]].append(r["score"])

        per_model_avg = {
            model: sum(scores) / len(scores)
            for model, scores in model_scores.items()
        }

        # Per-question averages
        question_scores: Dict[str, List[float]] = {}
        for r in responses:
            if r["score"] is not None:
                if r["question_id"] not in question_scores:
                    question_scores[r["question_id"]] = []
                question_scores[r["question_id"]].append(r["score"])

        per_question_avg = {
            question: sum(scores) / len(scores)
            for question, scores in question_scores.items()
        }

        return {
            "overall_average": overall_avg,
            "per_model_average": per_model_avg,
            "per_question_average": per_question_avg,
            "total_responses": len(responses),
            "scored_responses": len(scores)
        }
