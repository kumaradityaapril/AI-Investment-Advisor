from unittest.mock import MagicMock, patch

from app.services.embedding_service import (
    EmbeddingGenerationError,
    generate_document_embeddings,
    generate_query_embedding,
)


def make_embedding(values):
    embedding = MagicMock()
    embedding.values = values
    return embedding


@patch("app.services.embedding_service._get_gemini_client")
def test_document_embeddings(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client
    mock_client.models.embed_content.return_value.embeddings = [
        make_embedding([3.0] * 768),
        make_embedding([4.0] * 768),
    ]

    result = generate_document_embeddings(
        ["Revenue increased.", "Profit decreased."]
    )

    assert len(result) == 2
    assert len(result[0]) == 768
    magnitude = sum(value * value for value in result[0]) ** 0.5
    assert abs(magnitude - 1.0) < 1e-6


@patch("app.services.embedding_service._get_gemini_client")
def test_query_embedding(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client
    mock_client.models.embed_content.return_value.embeddings = [
        make_embedding([2.0] * 768),
    ]

    result = generate_query_embedding("What was the annual revenue?")

    assert len(result) == 768
    magnitude = sum(value * value for value in result) ** 0.5
    assert abs(magnitude - 1.0) < 1e-6

    # Verify task_type was RETRIEVAL_QUERY
    call_args = mock_client.models.embed_content.call_args
    assert call_args is not None
    config = call_args.kwargs.get("config")
    assert config is not None
    assert config.task_type == "RETRIEVAL_QUERY"


def test_empty_texts():
    assert generate_document_embeddings([]) == []


def test_invalid_inputs():
    try:
        generate_document_embeddings([""])
        assert False, "Expected ValueError for empty string"
    except ValueError:
        pass

    try:
        generate_document_embeddings(["Valid", "   "])
        assert False, "Expected ValueError for whitespace-only string"
    except ValueError:
        pass

    try:
        generate_query_embedding("")
        assert False, "Expected ValueError for empty query"
    except ValueError:
        pass

    try:
        generate_document_embeddings(["text"], batch_size=0)
        assert False, "Expected ValueError for batch_size=0"
    except ValueError:
        pass


@patch("app.services.embedding_service._get_gemini_client")
def test_zero_magnitude_error(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client
    mock_client.models.embed_content.return_value.embeddings = [
        make_embedding([0.0] * 768),
    ]

    try:
        generate_document_embeddings(["Sample text"])
        assert False, "Expected EmbeddingGenerationError for zero magnitude"
    except EmbeddingGenerationError:
        pass


@patch("app.services.embedding_service._get_gemini_client")
def test_dimension_mismatch(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client
    mock_client.models.embed_content.return_value.embeddings = [
        make_embedding([1.0] * 512),
    ]

    try:
        generate_document_embeddings(["Sample text"])
        assert False, "Expected EmbeddingGenerationError for dimension mismatch"
    except EmbeddingGenerationError:
        pass


@patch("app.services.embedding_service._get_gemini_client")
def test_batching(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    def side_effect(model, contents, config):
        resp = MagicMock()
        resp.embeddings = [make_embedding([1.0] * 768) for _ in contents]
        return resp

    mock_client.models.embed_content.side_effect = side_effect

    texts = [f"Text chunk {i}" for i in range(5)]
    result = generate_document_embeddings(texts, batch_size=2)

    assert len(result) == 5
    assert mock_client.models.embed_content.call_count == 3


if __name__ == "__main__":
    test_document_embeddings()
    test_query_embedding()
    test_empty_texts()
    test_invalid_inputs()
    test_zero_magnitude_error()
    test_dimension_mismatch()
    test_batching()
    print("All embedding service tests passed.")

