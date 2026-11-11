from typing import TypedDict


class DocumentChunk(TypedDict):
    chunk_index: int
    page_number: int
    content: str


def chunk_document_pages(
    pages: list[dict[str, str | int]],
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
) -> list[DocumentChunk]:
    """
    Split page text into overlapping chunks.
    Chunk size and overlap are measured in characters.
    Each chunk keeps the original PDF page number.
    """
    if chunk_size <= 0:
        raise ValueError("Chunk size must be greater than zero.")
    if chunk_overlap < 0:
        raise ValueError("Chunk overlap cannot be negative.")
    if chunk_overlap >= chunk_size:
        raise ValueError("Chunk overlap must be smaller than chunk size.")

    chunks: list[DocumentChunk] = []
    chunk_index = 0
    step = chunk_size - chunk_overlap

    for page in pages:
        page_number = int(page["page_number"])
        text = str(page["text"])

        if not text:
            continue

        start = 0
        text_length = len(text)

        while start < text_length:
            end = min(start + chunk_size, text_length)
            chunk_content = text[start:end]

            chunks.append(
                DocumentChunk(
                    chunk_index=chunk_index,
                    page_number=page_number,
                    content=chunk_content,
                )
            )
            chunk_index += 1

            if end >= text_length:
                break

            start += step

    return chunks

