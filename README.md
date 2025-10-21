# llmzoomcamp-project

### Description
Large language models are powerful at generating answers but often produce incorrect or fabricated information when they lack access to reliable context. 
To improve factual accuracy and contextual grounding, it is essential to combine generative models with high-quality, domain-relevant knowledge sources.

This project uses the SQuAD v2 dataset as the knowledge base for a Retrieval-Augmented Generation (RAG) system.
The goal is to build a question-answering pipeline that retrieves the most relevant passages from SQuAD v2 and generates context-aware,
trustworthy responses to user queries. By leveraging this dataset, the project aims to demonstrate how integrating retrieval with generation can enhance answer relevance,
reduce hallucinations, and enable the system to recognize when no valid answer exists in the provided context.

A production-ready Retrieval-Augmented Generation (RAG) chat application built with Streamlit, PostgreSQL, Qdrant vector database, and Grafana monitoring.

## 🚀 Features

- **Interactive Chat Interface** - Ask questions about the SQuAD v2 dataset
- **Hybrid Search** - Combines dense (semantic) and sparse (keyword) search using Qdrant
- **Real-time Monitoring** - Grafana dashboards for performance metrics and analytics
- **Production Logging** - PostgreSQL database tracks all interactions and metrics
- **Docker Orchestration** - Full containerized setup with health checks

## 📋 Prerequisites

- Docker and Docker Compose installed
- Python 3.11+ (if running ingestion locally)
- Groq API key (for LLM inference)

## ⚡ Quick Start (Use Existing Knowledge Base)

If you want to use the pre-built knowledge base, follow these steps:

### 1. Clone the Repository
```bash
git clone <your-repo-url>
cd llm-project
```

### 2. Set Up Environment Variables
```bash
# Copy the environment template
cp .env.example .env

# Edit the .env file and add your API keys
nano .env
```

**Required environment variables in `.env`:**
```bash
# Database Configuration
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=llm_project
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

# Qdrant Configuration
QDRANT_HOST=qdrant
QDRANT_PORT=6333

# API Keys (REQUIRED - add your actual keys)
GROQ_API_KEY=your_actual_groq_api_key_here

# Application Configuration
STREAMLIT_SERVER_PORT=8501
LOG_LEVEL=INFO
```

### 3. Start the Application
```bash
# Start all services in detached mode
docker-compose up -d

# Check if all services are healthy
docker-compose ps
```

### 4. Access the Application
- **Chat Application**: http://localhost:8501
- **Grafana Dashboard**: http://localhost:3000 (admin/admin)
- **Qdrant Console**: http://localhost:6333/dashboard

## 🔧 Custom Knowledge Base Setup

If you want to ingest your own data from the SQuAD v2 dataset:

### 1. Install Dependencies
```bash
# Install uv package manager
pip install uv

# Create and sync virtual environment with dependencies
uv sync

# Activate the virtual environment
source .venv/bin/activate
```

### 2. Start Qdrant Service First
**Important**: Ensure you have completed Step 2 (environment variables setup) before proceeding.

```bash
# Start only Qdrant (required for ingestion)
docker-compose up -d qdrant

# Verify Qdrant is running and healthy
docker-compose ps qdrant
```

### 3. Run Data Ingestion
```bash
# Run ingestion script (modify records count as needed)
python ingest.py
```

**Note**: You can modify the number of records to ingest by editing the parameters in [`ingest.py`](ingest.py).

### 4. Update Collection Name
After ingestion, update the collection name in [`app/llm_assistant.py`](app/llm_assistant.py):

```python
# Change this line to match your collection name from ingest.py
COLLECTION_NAME = "your_collection_name_here"
```

### 5. Start All Services
```bash
# Now start all services including the updated collection
docker-compose up -d
```

## 📊 Monitoring and Analytics

The application includes comprehensive monitoring via Grafana:

### Key Metrics Tracked:
- **Response Times** - Average, P95, P99 response latencies
- **Token Usage** - Total tokens consumed and trends
- **Question Volume** - Daily/hourly question counts
- **User Feedback** - Ratings and satisfaction scores
- **System Health** - Database and vector store performance

### Access Dashboards:
1. Open http://localhost:3000
2. Login with `admin` / `admin`
3. Navigate to "LLM RAG System Dashboard"

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Streamlit     │    │   PostgreSQL    │    │     Qdrant      │
│   (Frontend)    │◄──►│   (Logging)     │    │ (Vector Store)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                        │                        │
         └────────────────────────┼────────────────────────┘
                                  │
                          ┌─────────────────┐
                          │     Grafana     │
                          │  (Monitoring)   │
                          └─────────────────┘
```

### Components:
- **Streamlit**: Web interface for chat interactions
- **PostgreSQL**: Stores questions, answers, feedback, and metrics
- **Qdrant**: Vector database for similarity search and retrieval
- **Grafana**: Real-time monitoring and analytics dashboards

## 🔍 How It Works

1. **User asks a question** in the Streamlit interface
2. **Question is logged** to PostgreSQL with session tracking
3. **Hybrid search** retrieves relevant context from Qdrant:
   - Dense embeddings for semantic similarity
   - Sparse embeddings (BM25) for keyword matching
4. **LLM generates answer** using retrieved context via Groq API
5. **Response and metrics** are logged to PostgreSQL
6. **User can provide feedback** which is stored for analytics
7. **Grafana displays** real-time performance metrics

## 🛠️ Development

### Project Structure
```
llm-project/
├── app/
│   ├── app.py              # Main Streamlit application
│   ├── llm_assistant.py    # RAG logic and LLM integration
│   ├── database.py         # PostgreSQL logging functions
│   └── init.sql           # Database schema initialization
├── grafana/
│   ├── dashboards/        # Grafana dashboard definitions
│   └── provisioning/      # Automated Grafana setup
├── docker-compose.yml     # Service orchestration
├── Dockerfile            # Streamlit app container
├── ingest.py            # Data ingestion script
├── pyproject.toml       # Python dependencies
└── .env.example         # Environment template
```

### Key Files:
- **[`app/app.py`](app/app.py)**: Main chat interface with session management
- **[`app/llm_assistant.py`](app/llm_assistant.py)**: RAG pipeline with hybrid search
- **[`ingest.py`](ingest.py)**: SQuAD v2 dataset ingestion to Qdrant
- **[`app/database.py`](app/database.py)**: PostgreSQL logging and metrics collection


## 📚 API Documentation

### Environment Variables Reference:

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `GROQ_API_KEY` | Groq API key for LLM inference | - | ✅ |
| `POSTGRES_HOST` | PostgreSQL hostname | `postgres` | No |
| `POSTGRES_PORT` | PostgreSQL port | `5432` | No |
| `POSTGRES_DB` | Database name | `llm_project` | No |
| `POSTGRES_USER` | Database user | `postgres` | No |
| `POSTGRES_PASSWORD` | Database password | `postgres` | No |
| `QDRANT_HOST` | Qdrant hostname | `qdrant` | No |
| `QDRANT_PORT` | Qdrant port | `6333` | No |

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- SQuAD v2 dataset for training data
- Qdrant for vector search capabilities
- Groq for fast LLM inference
- Streamlit for the interactive interface