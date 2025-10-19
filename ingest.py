import uuid

import pandas as pd
from datasets import load_dataset
from qdrant_client import QdrantClient, models

from utils import clean_data

DENSE_MODEL = "jinaai/jina-embeddings-v2-small-en"
SPARSE_MODEL = "Qdrant/bm25"
COLLECTION_NAME = "squad_v2"
EMBEDDING_DIM = 512

client = QdrantClient("http://localhost", port=6333)


def load_data(n: int = 1000) -> list[dict]:
    full_data = load_dataset("squad_v2", split="train")
    shuffled_data = full_data.shuffle(seed=42)
    data_df = pd.DataFrame(shuffled_data)

    data = data_df.head(n)

    return data.to_dict(orient="records")


def prepare_data(data: list[dict]) -> list[dict]:
    cleaned_data = clean_data(data)

    embedding_documents = []

    for doc in cleaned_data:
        embedding_text = f"Question: {doc['question']} Context: {doc['context']}"

        answer = ""
        if doc["answers"]["text"] and len(doc["answers"]["text"]) > 0:
            answer = doc["answers"]["text"][0].replace('"', "")

        embedding_documents.append(
            {
                "text": embedding_text,
                "metadata": {
                    "title": doc["title"],
                    "context": doc["context"].replace("\n", " "),
                    "question": doc["question"].replace("\n", " "),
                    "answer": answer,
                    "has_answer": bool(answer),
                },
            }
        )

    return embedding_documents


def create_embeddings(documents: list[dict]) -> list[dict]:
    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config={
            "jina-small": models.VectorParams(
                size=EMBEDDING_DIM, distance=models.Distance.COSINE
            )
        },
        sparse_vectors_config={
            "bm25": models.SparseVectorParams(modifier=models.Modifier.IDF)
        },
    )
    points = []
    for record in documents:
        point = models.PointStruct(
            id=uuid.uuid4().hex,
            vector={
                "bm25": models.Document(text=record["text"], model=SPARSE_MODEL),
                "jina-small": models.Document(text=record["text"], model=DENSE_MODEL),
            },
            payload={
                "metadata": record["metadata"],
            },
        )
        points.append(point)

    return points


def ingest_data(points: list[dict]):
    print("Ingesting data into Qdrant...")
    client.upsert(collection_name=COLLECTION_NAME, points=points)
    print(f"Ingested {len(points)} points into collection '{COLLECTION_NAME}'")


def main():
    data = load_data()
    prepared_data = prepare_data(data)
    points = create_embeddings(prepared_data)
    ingest_data(points)


if __name__ == "__main__":
    main()
