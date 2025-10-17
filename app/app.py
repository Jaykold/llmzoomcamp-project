import os

import streamlit as st
from qdrant_client import QdrantClient
from sqlalchemy import create_engine

# Page configuration
st.set_page_config(page_title="LLM RAG System", page_icon="🤖", layout="wide")

# Title
st.title("🤖 LLM RAG Question Answering System")
st.markdown("Ask questions and get answers from the SQuAD v2 dataset using RAG")

# Sidebar for configuration
st.sidebar.header("Configuration")

# Environment variables with defaults
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "llm_project")
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")

QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = os.getenv("QDRANT_PORT", "6333")

# Connection status
st.sidebar.subheader("Connection Status")

# Test Postgres connection
try:
    postgres_url = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    engine = create_engine(postgres_url)
    with engine.connect() as conn:
        conn.execute("SELECT 1")
    st.sidebar.success("✅ PostgreSQL Connected")
except Exception as e:
    st.sidebar.error(f"❌ PostgreSQL Error: {str(e)}")

# Test Qdrant connection
try:
    qdrant_client = QdrantClient(host=QDRANT_HOST, port=int(QDRANT_PORT))
    collections = qdrant_client.get_collections()
    st.sidebar.success("✅ Qdrant Connected")
    st.sidebar.info(f"Collections: {len(collections.collections)}")
except Exception as e:
    st.sidebar.error(f"❌ Qdrant Error: {str(e)}")

# Main interface
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Ask a Question")
    question = st.text_area(
        "Enter your question here:",
        placeholder="What is the capital of France?",
        height=100,
    )

    if st.button("Get Answer", type="primary"):
        if question:
            with st.spinner("Processing your question..."):
                # Placeholder for RAG pipeline
                st.info("🚧 RAG pipeline implementation coming soon!")
                st.write(f"**Question:** {question}")
                st.write(
                    "**Answer:** This is where the RAG-generated answer will appear."
                )
        else:
            st.warning("Please enter a question.")

with col2:
    st.subheader("System Info")
    st.json(
        {
            "Postgres Host": POSTGRES_HOST,
            "Qdrant Host": QDRANT_HOST,
            "Status": "Running",
        }
    )

# Footer
st.markdown("---")
st.markdown("Built with Streamlit, PostgreSQL, and Qdrant for LLM ZoomCamp Project")
