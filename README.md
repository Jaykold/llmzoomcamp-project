# llmzoomcamp-project

### Description
Large language models are powerful at generating answers but often produce incorrect or fabricated information when they lack access to reliable context. 
To improve factual accuracy and contextual grounding, it is essential to combine generative models with high-quality, domain-relevant knowledge sources.

This project uses the SQuAD v2 dataset as the knowledge base for a Retrieval-Augmented Generation (RAG) system.
The goal is to build a question-answering pipeline that retrieves the most relevant passages from SQuAD v2 and generates context-aware,
trustworthy responses to user queries. By leveraging this dataset, the project aims to demonstrate how integrating retrieval with generation can enhance answer relevance,
reduce hallucinations, and enable the system to recognize when no valid answer exists in the provided context.