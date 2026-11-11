from app.services.document_chunking_service import chunk_document_pages


def test_chunks_preserve_page_numbers():
    pages = [
        {
            "page_number": 1,
            "text": "A" * 1500,
        },
        {
            "page_number": 2,
            "text": "B" * 500,
        },
    ]
    chunks = chunk_document_pages(
        pages,
        chunk_size=1000,
        chunk_overlap=200,
    )
    assert len(chunks) == 3
    assert chunks[0]["page_number"] == 1
    assert chunks[1]["page_number"] == 1
    assert chunks[2]["page_number"] == 2
    print("PASS: Chunks preserve page numbers")


def test_chunk_overlap():
    pages = [
        {
            "page_number": 1,
            "text": "A" * 1500,
        }
    ]
    chunks = chunk_document_pages(
        pages,
        chunk_size=1000,
        chunk_overlap=200,
    )
    assert len(chunks) == 2
    assert chunks[0]["content"][-200:] == chunks[1]["content"][:200]
    print("PASS: Chunk overlap verified")


def test_invalid_chunk_arguments():
    pages = [{"page_number": 1, "text": "Hello world"}]
    try:
        chunk_document_pages(pages, chunk_size=0)
        assert False, "Expected ValueError for chunk_size=0"
    except ValueError:
        pass

    try:
        chunk_document_pages(pages, chunk_size=100, chunk_overlap=-1)
        assert False, "Expected ValueError for negative overlap"
    except ValueError:
        pass

    try:
        chunk_document_pages(pages, chunk_size=100, chunk_overlap=100)
        assert False, "Expected ValueError for overlap >= size"
    except ValueError:
        pass
    print("PASS: Invalid chunk arguments handled correctly")


if __name__ == "__main__":
    test_chunks_preserve_page_numbers()
    test_chunk_overlap()
    test_invalid_chunk_arguments()
    print("All document chunking tests passed successfully!")

