import os
import uuid

import streamlit as st
from database import get_system_stats, log_answer, log_feedback, log_question
from llm_assistant import rag
from qdrant_client import QdrantClient
from sqlalchemy import create_engine

# Page configuration
st.set_page_config(page_title="LLM RAG Chat", page_icon="🤖", layout="wide")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

# Environment variables with defaults
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "llm_project")
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = os.getenv("QDRANT_PORT", "6333")

# Sidebar
st.sidebar.header("🔧 System Status")

# Connection status
postgres_connected = False
qdrant_connected = False

try:
    postgres_url = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    engine = create_engine(postgres_url)
    with engine.connect() as conn:
        conn.execute("SELECT 1")
    st.sidebar.success("✅ PostgreSQL Connected")
    postgres_connected = True
except Exception as e:
    st.sidebar.error(f"❌ PostgreSQL: {str(e)[:50]}...")

try:
    qdrant_client = QdrantClient(host=QDRANT_HOST, port=int(QDRANT_PORT))
    collections = qdrant_client.get_collections()
    st.sidebar.success("✅ Qdrant Connected")
    st.sidebar.info(f"Collections: {len(collections.collections)}")
    qdrant_connected = True
except Exception as e:
    st.sidebar.error(f"❌ Qdrant: {str(e)[:50]}...")

# System metrics
if postgres_connected:
    st.sidebar.subheader("📊 Today's Metrics")
    try:
        stats = get_system_stats()
        st.sidebar.metric("Questions Asked", stats["total_questions"])
        st.sidebar.metric("Avg Response Time", f"{stats['avg_response_time']}ms")
        st.sidebar.metric("Avg Tokens Used", int(stats["avg_tokens"]))
        st.sidebar.metric("Fast Responses (<1s)", stats["fast_responses"])
    except Exception:
        st.sidebar.error("Metrics unavailable")

# Clear chat button
if st.sidebar.button("🗑️ Clear Chat"):
    st.session_state.messages = []
    st.rerun()

# Main chat interface
st.title("🤖 LLM RAG Chat Assistant")
st.markdown("Ask questions about the SQuAD v2 dataset using Retrieval-Augmented Generation")

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        
        # Show metrics for assistant messages
        if message["role"] == "assistant" and "metrics" in message:
            with st.expander("📈 Response Metrics"):
                metrics = message["metrics"]
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Time", f"{metrics.get('total_time_ms', 0)}ms")
                    st.metric("Retrieval Time", f"{metrics.get('retrieval_time_ms', 0)}ms")
                with col2:
                    st.metric("Generation Time", f"{metrics.get('generation_time_ms', 0)}ms")
                    st.metric("Docs Retrieved", metrics.get('retrieved_docs_count', 0))
                with col3:
                    st.metric("Total Tokens", metrics.get('total_tokens', 0))
                    st.metric("Model", metrics.get('model_used', 'N/A'))

# Chat input
if prompt := st.chat_input("Ask me anything about the dataset..."):
    # Check if both services are connected
    if not (postgres_connected and qdrant_connected):
        st.error("⚠️ Cannot process questions - database services not available")
        st.stop()
    
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Generate response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                # Log question to database
                question_id = log_question(
                    question_text=prompt,
                    user_id="streamlit_user",
                    session_id=st.session_state.session_id
                )
                
                # Get RAG response
                result = rag(prompt)
                
                # Display answer
                st.markdown(result["answer"])
                
                # Log answer to database
                answer_id = log_answer(
                    question_id=question_id,
                    answer_text=result["answer"],
                    context_used=result["context_used"],
                    model_used=result["metrics"]["model_used"],
                    confidence_score=None,  # Not available from Groq
                    retrieval_time_ms=result["metrics"]["retrieval_time_ms"],
                    generation_time_ms=result["metrics"]["generation_time_ms"],
                    total_time_ms=result["metrics"]["total_time_ms"],
                    qdrant_collection=result["metrics"]["qdrant_collection"],
                    retrieved_docs_count=result["metrics"]["retrieved_docs_count"],
                    prompt_tokens=result["metrics"]["prompt_tokens"],
                    completion_tokens=result["metrics"]["completion_tokens"],
                    total_tokens=result["metrics"]["total_tokens"]
                )
                
                # Show metrics
                with st.expander("📈 Response Metrics"):
                    metrics = result["metrics"]
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total Time", f"{metrics['total_time_ms']}ms")
                        st.metric("Retrieval Time", f"{metrics['retrieval_time_ms']}ms")
                    with col2:
                        st.metric("Generation Time", f"{metrics['generation_time_ms']}ms")
                        st.metric("Docs Retrieved", metrics['retrieved_docs_count'])
                    with col3:
                        st.metric("Total Tokens", metrics['total_tokens'])
                        st.metric("Model", metrics['model_used'])
                
                # Add assistant message to chat history
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": result["answer"],
                    "metrics": result["metrics"],
                    "answer_id": answer_id
                })
                
                # Quick feedback buttons
                st.markdown("**Was this helpful?**")
                col1, col2 = st.columns([1, 1])
                with col1:
                    if st.button("👍 Yes", key=f"yes_{answer_id}"):
                        log_feedback(answer_id, rating=5, is_helpful=True)
                        st.success("Thanks for the feedback!")
                with col2:
                    if st.button("👎 No", key=f"no_{answer_id}"):
                        log_feedback(answer_id, rating=2, is_helpful=False)
                        st.success("Thanks for the feedback!")
                
            except Exception as e:
                st.error(f"Error processing your question: {str(e)}")

# Footer
st.markdown("---")
st.markdown(
    "🚀 **Built with Streamlit + PostgreSQL + Qdrant** | "
    f"Session: `{st.session_state.session_id[:8]}...`"
)
