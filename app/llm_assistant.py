import os

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


def rrf_search(query: str, limit: int = 1) -> list[models.ScoredPoint]:
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

    return results.points


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


def llm_response(prompt, model: str = "openai/gpt-oss-20b") -> str:
    client = Groq(api_key=groq_api_key)
    response = client.chat.completions.create(messages=prompt, model=model)

    return response.choices[0].message.content


def rag(query):
    search_results = rrf_search(query)
    prompt = build_prompt(query, search_results)
    answer = llm_response(prompt)

    return answer


def main():
    question = "What provides critical support for drug discovery and the availability of economic resources?"
    print("This is groq api key", qdrant_host)
    answer = rag(question)
    print(f"Question: {question}\nAnswer: {answer}")


if __name__ == "__main__":
    main()
