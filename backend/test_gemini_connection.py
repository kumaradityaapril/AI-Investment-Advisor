import math

from app.core.config import settings
from app.services.embedding_service import (
    generate_document_embeddings,
    generate_query_embedding,
)


def main():
    print("Testing Gemini embedding API...")
    # 1. Verify configuration without printing the API key.
    assert settings.gemini_api_key.strip(), "Gemini API key is missing."
    print(f"Model: {settings.embedding_model}")
    print(f"Dimensions: {settings.embedding_dimensions}")

    # 2. Generate an actual document embedding.
    document_text = (
        "The company reported annual revenue of INR 500000 "
        "and net profit of INR 75000."
    )
    document_embeddings = generate_document_embeddings([document_text])
    document_vector = document_embeddings[0]
    assert len(document_vector) == settings.embedding_dimensions
    document_norm = math.sqrt(sum(value * value for value in document_vector))
    assert abs(document_norm - 1.0) < 1e-5
    print("PASS: Document embedding generated.")
    print(f"Document vector dimensions: {len(document_vector)}")
    print(f"Document vector norm: {document_norm:.6f}")

    # 3. Generate an actual query embedding.
    query_text = "What was the company's annual revenue and profit?"
    query_vector = generate_query_embedding(query_text)
    assert len(query_vector) == settings.embedding_dimensions
    query_norm = math.sqrt(sum(value * value for value in query_vector))
    assert abs(query_norm - 1.0) < 1e-5
    print("PASS: Query embedding generated.")
    print(f"Query vector dimensions: {len(query_vector)}")
    print(f"Query vector norm: {query_norm:.6f}")

    print("\nGemini API smoke test passed successfully!")


if __name__ == "__main__":
    main()

