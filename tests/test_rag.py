from pathlib import Path

from basketball_api.rag import MAX_CHUNK_CHARACTERS, chunk_text, load_documents


def test_chunk_text_is_bounded_and_overlaps_paragraph_boundaries() -> None:
    first = "a" * 700
    second = "b" * 700

    chunks = chunk_text(f"{first}\n\n{second}")

    assert len(chunks) == 2
    assert all(len(chunk) <= MAX_CHUNK_CHARACTERS for chunk in chunks)
    assert chunks[1].startswith("a" * 150)


def test_load_documents_reads_required_frontmatter() -> None:
    documents = load_documents(Path("documents"))

    assert len(documents) >= 8
    assert {document.id for document in documents} >= {"shai-scouting", "drop-coverage"}
