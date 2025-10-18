"""
Database logging functions for the RAG chat application
"""

import os
import uuid
from typing import Optional

from sqlalchemy import create_engine, text


def get_db_connection():
    """Get PostgreSQL connection using environment variables"""
    POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
    POSTGRES_DB = os.getenv("POSTGRES_DB", "llm_project")
    POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")

    postgres_url = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    return create_engine(postgres_url)


def log_question(
    question_text: str, user_id: str = "anonymous", session_id: str = None
) -> str:
    """Log a question to the database and return the question_id"""
    engine = get_db_connection()
    question_id = str(uuid.uuid4())

    with engine.connect() as conn:
        conn.execute(
            text("""
            INSERT INTO questions (id, question_text, user_id, session_id)
            VALUES (:id, :question_text, :user_id, :session_id)
        """),
            {
                "id": question_id,
                "question_text": question_text,
                "user_id": user_id,
                "session_id": session_id,
            },
        )
        conn.commit()

    return question_id


def log_answer(
    question_id: str,
    answer_text: str,
    model_used: str,
    confidence_score: Optional[float],
    retrieval_time_ms: int,
    generation_time_ms: int,
    total_time_ms: int,
    qdrant_collection: str,
    retrieved_docs_count: int,
    total_tokens: int,
) -> str:
    """Log an answer with all metrics to the database"""
    engine = get_db_connection()
    answer_id = str(uuid.uuid4())

    with engine.connect() as conn:
        conn.execute(
            text("""
            INSERT INTO answers (
                id, question_id, answer_text, model_used, 
                confidence_score, retrieval_time_ms, generation_time_ms, 
                total_time_ms, qdrant_collection, retrieved_docs_count, total_tokens
            )
            VALUES (
                :id, :question_id, :answer_text, :model_used,
                :confidence_score, :retrieval_time_ms, :generation_time_ms,
                :total_time_ms, :qdrant_collection, :retrieved_docs_count, :total_tokens
            )
        """),
            {
                "id": answer_id,
                "question_id": question_id,
                "answer_text": answer_text,
                "model_used": model_used,
                "confidence_score": confidence_score,
                "retrieval_time_ms": retrieval_time_ms,
                "generation_time_ms": generation_time_ms,
                "total_time_ms": total_time_ms,
                "qdrant_collection": qdrant_collection,
                "retrieved_docs_count": retrieved_docs_count,
                "total_tokens": total_tokens,
            },
        )
        conn.commit()

    return answer_id


def log_feedback(
    answer_id: str, rating: int, feedback_text: str = None, is_helpful: bool = None
):
    """Log user feedback for an answer"""
    engine = get_db_connection()

    with engine.connect() as conn:
        conn.execute(
            text("""
            INSERT INTO feedback (answer_id, rating, feedback_text, is_helpful)
            VALUES (:answer_id, :rating, :feedback_text, :is_helpful)
        """),
            {
                "answer_id": answer_id,
                "rating": rating,
                "feedback_text": feedback_text,
                "is_helpful": is_helpful,
            },
        )
        conn.commit()


def get_recent_conversations(limit: int = 10):
    """Get recent conversations for chat history"""
    engine = get_db_connection()

    with engine.connect() as conn:
        result = conn.execute(
            text("""
            SELECT q.question_text, a.answer_text, q.created_at
            FROM questions q
            LEFT JOIN answers a ON q.id = a.question_id
            ORDER BY q.created_at DESC
            LIMIT :limit
        """),
            {"limit": limit},
        )

        return [
            {"question": row[0], "answer": row[1], "timestamp": row[2]}
            for row in result.fetchall()
        ]


def get_system_stats():
    """Get system performance statistics"""
    engine = get_db_connection()

    with engine.connect() as conn:
        result = conn.execute(
            text("""
            SELECT 
                COUNT(*) as total_questions,
                AVG(total_time_ms) as avg_response_time,
                AVG(total_tokens) as avg_tokens,
                COUNT(CASE WHEN total_time_ms < 1000 THEN 1 END) as fast_responses
            FROM answers
            WHERE created_at >= NOW() - INTERVAL '24 hours'
        """)
        )

        row = result.fetchone()
        if row:
            return {
                "total_questions": row[0] or 0,
                "avg_response_time": round(row[1] or 0, 2),
                "avg_tokens": round(row[2] or 0, 2),
                "fast_responses": row[3] or 0,
            }
        return {
            "total_questions": 0,
            "avg_response_time": 0,
            "avg_tokens": 0,
            "fast_responses": 0,
        }
