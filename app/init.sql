-- Initialize database for LLM RAG project
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create tables for storing questions, answers, and feedback
CREATE TABLE IF NOT EXISTS questions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    question_text TEXT NOT NULL,
    user_id VARCHAR(255),
    session_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS answers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    question_id UUID REFERENCES questions(id),
    answer_text TEXT NOT NULL,
    model_used VARCHAR(100) DEFAULT 'groq-llama',
    confidence_score FLOAT,
    retrieval_time_ms INTEGER,
    generation_time_ms INTEGER,
    total_time_ms INTEGER,
    qdrant_collection VARCHAR(100) DEFAULT 'squad_v2',
    retrieved_docs_count INTEGER DEFAULT 5,
    total_tokens INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS feedback (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    answer_id UUID REFERENCES answers(id),
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    feedback_text TEXT,
    is_helpful BOOLEAN,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_questions_created_at ON questions(created_at);
CREATE INDEX IF NOT EXISTS idx_questions_session_id ON questions(session_id);
CREATE INDEX IF NOT EXISTS idx_answers_question_id ON answers(question_id);
CREATE INDEX IF NOT EXISTS idx_answers_created_at ON answers(created_at);
CREATE INDEX IF NOT EXISTS idx_feedback_answer_id ON feedback(answer_id);

-- Create views for analytics
CREATE OR REPLACE VIEW question_answer_summary AS
SELECT 
    q.id as question_id,
    q.question_text,
    q.user_id,
    q.session_id,
    q.created_at as question_time,
    a.answer_text,
    a.model_used,
    a.confidence_score,
    a.total_time_ms,
    f.rating,
    f.is_helpful
FROM questions q
LEFT JOIN answers a ON q.id = a.question_id
LEFT JOIN feedback f ON a.id = f.answer_id
ORDER BY q.created_at DESC;

-- Create view for system performance metrics
CREATE OR REPLACE VIEW system_performance AS
SELECT 
    DATE(created_at) as date,
    COUNT(*) as total_questions,
    AVG(total_time_ms) as avg_response_time,
    AVG(confidence_score) as avg_confidence,
    COUNT(CASE WHEN total_time_ms < 1000 THEN 1 END) as fast_responses,
    COUNT(CASE WHEN total_time_ms >= 1000 THEN 1 END) as slow_responses
FROM answers
GROUP BY DATE(created_at)
ORDER BY date DESC;
