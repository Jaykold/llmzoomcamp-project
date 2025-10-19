# Data Architecture and Ingestion Guide

## Overview

Your RAG system uses a **dual-database architecture**:

1. **Qdrant (Vector Database)** - Stores the actual SQuAD v2 knowledge base with embeddings
2. **PostgreSQL (Relational Database)** - Stores user interactions, system metrics, and logs

## Current init.sql Implementation

### Purpose
The `init.sql` file initializes PostgreSQL for **operational data**, not the knowledge base itself. It creates tables for:

### Core Tables

#### 1. `questions` - User Query Tracking
```sql
CREATE TABLE questions (
    id UUID PRIMARY KEY,                 -- Unique question identifier
    question_text TEXT NOT NULL,         -- The actual question asked
    user_id VARCHAR(255),               -- User identifier (optional)
    session_id VARCHAR(255),            -- Session tracking
    created_at TIMESTAMP DEFAULT NOW()  -- When question was asked
);
```

#### 2. `answers` - RAG System Responses
```sql
CREATE TABLE answers (
    id UUID PRIMARY KEY,                    -- Unique answer identifier
    question_id UUID,                       -- Links to original question
    answer_text TEXT NOT NULL,              -- Generated answer
    context_used TEXT,                      -- Retrieved context snippets
    model_used VARCHAR(100),                -- LLM model name
    confidence_score FLOAT,                 -- System confidence (0-1)
    retrieval_time_ms INTEGER,              -- Time to retrieve context
    generation_time_ms INTEGER,             -- Time to generate answer
    total_time_ms INTEGER,                  -- Total processing time
    qdrant_collection VARCHAR(100),         -- Which collection was queried
    retrieved_docs_count INTEGER,           -- How many docs retrieved
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### 3. `feedback` - User Ratings & Feedback
```sql
CREATE TABLE feedback (
    id UUID PRIMARY KEY,                    -- Unique feedback identifier
    answer_id UUID,                         -- Links to rated answer
    rating INTEGER CHECK (rating 1-5),     -- 1-5 star rating
    feedback_text TEXT,                     -- Optional text feedback
    is_helpful BOOLEAN,                     -- Quick helpful/not helpful
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Analytics Views

#### `question_answer_summary` - Complete Q&A with feedback
Shows questions, answers, and user ratings in one view for analysis.

#### `system_performance` - Daily performance metrics
Aggregates daily response times, confidence scores, and speed metrics.

## How Data Flows Through Your System

### 1. **Initial Data Ingestion** (One-time setup)

```
SQuAD v2 Dataset (squad_v2_600.json)
           ↓
    ingest.py processes data
           ↓
    Creates embeddings using:
    - Dense: jinaai/jina-embeddings-v2-small_en  
    - Sparse: Qdrant/bm25
           ↓
    Stores in Qdrant collection "squad_rag"
```

### 2. **Runtime Query Processing**

```
User asks question in Streamlit
           ↓
Question logged to PostgreSQL (questions table)
           ↓
Query vectorized and sent to Qdrant
           ↓
Qdrant returns relevant contexts
           ↓
LLM generates answer using retrieved context
           ↓
Answer + metrics logged to PostgreSQL (answers table)
           ↓
User provides feedback (optional)
           ↓
Feedback logged to PostgreSQL (feedback table)
```

## Key Files in Your Project

- **`data/squad_v2_600.json`** - Raw SQuAD v2 dataset (600 samples)
- **`ingest.py`** - Processes data and loads into Qdrant
- **`init.sql`** - Sets up PostgreSQL schema for tracking
- **`app.py`** - Streamlit frontend
- **`utils.py`** - Data cleaning utilities

## Running the Complete Ingestion

### Option 1: Docker Compose (Recommended)
```bash
# Start all services
docker-compose up -d

### Option 2: Local Development
```bash
# Start services locally
docker-compose up postgres qdrant -d


## Monitoring Your System

After ingestion, you can query PostgreSQL to see system health:

```sql
-- View system performance
SELECT * FROM system_performance;

-- See all questions and answers
SELECT * FROM question_answer_summary LIMIT 10;
```

## Data Architecture Benefits

1. **Separation of Concerns**: 
   - Qdrant = Fast semantic search over knowledge base
   - PostgreSQL = Structured data, analytics, user tracking

2. **Scalability**: 
   - Vector search scales independently from relational queries
   - Can add more knowledge bases to Qdrant without changing PostgreSQL schema

3. **Observability**: 
   - Full audit trail of user interactions
   - Performance metrics for optimization
   - User feedback for model improvement

4. **Analytics**: 
   - Built-in views for system performance analysis
   - Easy to build dashboards and reports
   - Track user satisfaction over time

The `init.sql` file creates the foundation for a production-ready RAG system with proper logging, metrics, and user feedback collection!
