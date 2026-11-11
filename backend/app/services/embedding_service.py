import math

from google import genai
from google.genai import types

from app.core.config import settings


class EmbeddingGenerationError(Exception):
    """Raised when Gemini embedding generation fails."""


def _get_gemini_client() -> genai.Client:
    """Create a Gemini client using the configured API key."""
    return genai.Client(api_key=settings.gemini_api_key)


def _normalize_embedding(values: list[float]) -> list[float]:
    """Apply L2 normalization to an embedding vector."""
    magnitude = math.sqrt(sum(value * value for value in values))
    if magnitude == 0:
        raise EmbeddingGenerationError(
            "Gemini returned a zero-magnitude embedding."
        )
    return [value / magnitude for value in values]


def generate_embeddings(
    texts: list[str],
    task_type: str,
    batch_size: int = 32,
) -> list[list[float]]:
    """
    Generate normalized Gemini embeddings for multiple texts.
    Documents should use RETRIEVAL_DOCUMENT.
    Search questions should use RETRIEVAL_QUERY.
    """
    if batch_size <= 0:
        raise ValueError("Batch size must be greater than zero.")
    if not texts:
        return []
    if any(not isinstance(text, str) or not text.strip() for text in texts):
        raise ValueError("All texts must be non-empty strings.")

    allowed_task_types = {
        "RETRIEVAL_DOCUMENT",
        "RETRIEVAL_QUERY",
    }
    if task_type not in allowed_task_types:
        raise ValueError("Unsupported embedding task type.")

    client = _get_gemini_client()
    all_embeddings: list[list[float]] = []

    try:
        for start in range(0, len(texts), batch_size):
            batch = texts[start : start + batch_size]
            response = client.models.embed_content(
                model=settings.embedding_model,
                contents=batch,
                config=types.EmbedContentConfig(
                    task_type=task_type,
                    output_dimensionality=settings.embedding_dimensions,
                ),
            )
            embeddings = getattr(response, "embeddings", None)
            if embeddings is None or len(embeddings) != len(batch):
                raise EmbeddingGenerationError(
                    "Gemini did not return the expected number of embeddings."
                )

            for embedding in embeddings:
                values = getattr(embedding, "values", None)
                if values is None:
                    raise EmbeddingGenerationError(
                        "Gemini returned an empty embedding."
                    )
                if len(values) != settings.embedding_dimensions:
                    raise EmbeddingGenerationError(
                        f"Expected {settings.embedding_dimensions} dimensions, "
                        f"but got {len(values)}."
                    )
                normalized = _normalize_embedding(values)
                all_embeddings.append(normalized)

        return all_embeddings

    except (EmbeddingGenerationError, ValueError):
        raise
    except Exception as exc:
        raise EmbeddingGenerationError(
            "Failed to generate embeddings from Gemini."
        ) from exc


def generate_document_embeddings(
    texts: list[str],
    batch_size: int = 32,
) -> list[list[float]]:
    """Generate normalized Gemini embeddings for document chunks."""
    return generate_embeddings(
        texts=texts,
        task_type="RETRIEVAL_DOCUMENT",
        batch_size=batch_size,
    )


def generate_query_embedding(query: str) -> list[float]:
    """Generate a normalized Gemini embedding for a search query."""
    if not isinstance(query, str) or not query.strip():
        raise ValueError("Query must be a non-empty string.")
    embeddings = generate_embeddings(
        texts=[query],
        task_type="RETRIEVAL_QUERY",
    )
    if not embeddings:
        raise EmbeddingGenerationError("Failed to generate query embedding.")
    return embeddings[0]

