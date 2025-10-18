import os
import time
from typing import Dict, List, Tuple

from dotenv import load_dotenv
from groq import Groq
from qdrant_client import QdrantClient, models

load_dotenv()

groq_api_key = os.getenv("GROQ_API_KEY1")
qdrant_host = os.getenv("QDRANT_HOST", "localhost")

qdrant_client = QdrantClient(f"http://{qdrant_host}", port=6333)
groq_client = Groq(api_key=groq_api_key)

dense_model = "jinaai/jina-embeddings-v2-small-en"
sparse_model = "Qdrant/bm25"
collection_name = "squad_rag"


def rrf_search(query: str, limit: int = 2):
    """Perform retrieval and capture timing metrics"""
    start_time = time.time()

    results = qdrant_client.query_points(
        collection_name=collection_name,
        prefetch=[
            models.Prefetch(
                query=models.Document(text=query, model=dense_model),
                using="jina-small",
                limit=(3 * limit),
            ),
            models.Prefetch(
                query=models.Document(text=query, model=sparse_model),
                using="bm25",
                limit=(3 * limit),
            ),
        ],
        # Fusion using Reciprocal Rank Fusion (RRF)
        query=models.FusionQuery(fusion=models.Fusion.RRF),
        with_payload=True,
        limit=limit,
    )

    end_time = time.time()
    retrieval_time_ms = int((end_time - start_time) * 1000)

    return {
        "points": results.points,
        "retrieval_time_ms": retrieval_time_ms,
        "retrieved_docs_count": len(results.points),
    }


def build_prompt(query, search_results: models.ScoredPoint) -> str:
    context = "\n\n".join(
        [
            f"{'Context:'.ljust(10)}{res.payload['metadata']['context']}\n"
            f"{'Question:'.ljust(10)}{res.payload['metadata']['question']}\n"
            f"{'Answer:'.ljust(10)}{res.payload['metadata']['answer']}\n"
            f"{'Has_answer:'.ljust(10)}{res.payload['metadata']['has_answer']}"
            for res in search_results
        ]
    )

    prompt = [
        {
            "role": "system",
            "content": """You are a precise and reliable assistant. Your goal is to answer the question using *only* the information provided in the CONTEXT. Do not guess or make up any information.
            Instructions:
            - If the `Has_answer` flag is False, check the context carefully for relevant details. If no answer is clearly supported, reply with: "I don't know. This is beyong my knowledge base."
            - If the answer *is* supported in the context, rephrase and present it clearly and concisely, ensuring it is directly grounded in the information provided.
            - Do not use any external knowledge or assumptions. Stick strictly to the *CONTEXT*.
            - Do not fabricate answers or speculate beyond the given information.""",
        },
        {
            "role": "user",
            "content": f"QUESTION:\n {query}\n CONTEXT:\n {context.strip()}",
        },
    ]

    return prompt


def llm_response(prompt, model: str = "openai/gpt-oss-20b"):
    """Generate LLM response and capture metrics"""
    start_time = time.time()

    client = Groq(api_key=groq_api_key)
    response = client.chat.completions.create(messages=prompt, model=model)

    end_time = time.time()
    generation_time_ms = int((end_time - start_time) * 1000)

    # Extract metrics from response
    usage = response.usage

    return {
        "content": response.choices[0].message.content,
        "metrics": {
            "total_tokens": usage.total_tokens,
            "generation_time_ms": generation_time_ms,
            "model_used": model,
        },
    }


def rag(query):
    """Complete RAG pipeline with comprehensive metrics"""
    start_time = time.time()

    # Retrieval phase
    search_results = rrf_search(query)

    # Generation phase
    prompt = build_prompt(query, search_results["points"])
    llm_result = llm_response(prompt)

    end_time = time.time()
    total_time_ms = int((end_time - start_time) * 1000)

    return {
        "answer": llm_result["content"],
        "metrics": {
            **llm_result["metrics"],
            "retrieval_time_ms": search_results["retrieval_time_ms"],
            "total_time_ms": total_time_ms,
            "retrieved_docs_count": search_results["retrieved_docs_count"],
            "qdrant_collection": collection_name,
        },
    }


def main():
    question = "Which letters remain distinct?"
    print("Testing RAG system...")
    result = rag(question)
    print(f"Question: {question}")
    print(f"Answer: {result['answer']}")
    print(f"Metrics: {result['metrics']}")


if __name__ == "__main__":
    main()
