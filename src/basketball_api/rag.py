# ruff: noqa: E501
"""Small, testable RAG primitives backed by PostgreSQL and pgvector."""

import hashlib
import json
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

import frontmatter

MAX_CHUNK_CHARACTERS = 1200
CHUNK_OVERLAP_CHARACTERS = 150


@dataclass(frozen=True)
class KnowledgeDocument:
    id: str
    title: str
    subject: str
    date: str | None
    source: str
    tags: list[str]
    content: str


@dataclass(frozen=True)
class RetrievedChunk:
    evidence_id: str
    document_id: str
    content: str
    similarity: float


class Embedder(Protocol):
    def embed(self, texts: Sequence[str]) -> list[list[float]]: ...


class Generator(Protocol):
    def generate(self, question: str, statistics: dict[str, Any], evidence: Sequence[RetrievedChunk]) -> str: ...


def load_documents(directory: Path) -> list[KnowledgeDocument]:
    """Load committed Markdown documents with required provenance frontmatter."""
    documents: list[KnowledgeDocument] = []
    for path in sorted(directory.glob("*.md")):
        post = frontmatter.load(path)
        required = ("title", "subject", "source", "tags")
        missing = [field for field in required if field not in post.metadata]
        if missing:
            raise ValueError(f"{path} is missing frontmatter: {', '.join(missing)}")
        documents.append(
            KnowledgeDocument(
                id=path.stem,
                title=str(post["title"]), subject=str(post["subject"]),
                date=str(post.get("date")) if post.get("date") else None,
                source=str(post["source"]), tags=list(post["tags"]), content=post.content.strip(),
            )
        )
    return documents


def chunk_text(text: str) -> list[str]:
    """Split paragraphs into bounded chunks, retaining a short boundary overlap."""
    paragraphs = [paragraph.strip() for paragraph in text.split("\n\n") if paragraph.strip()]
    chunks: list[str] = []
    current = ""
    for paragraph in paragraphs:
        if len(paragraph) > MAX_CHUNK_CHARACTERS:
            if current:
                chunks.append(current)
                current = ""
            chunks.extend(_split_long_paragraph(paragraph))
            continue
        candidate = f"{current}\n\n{paragraph}" if current else paragraph
        if len(candidate) <= MAX_CHUNK_CHARACTERS:
            current = candidate
        else:
            chunks.append(current)
            current = f"{current[-CHUNK_OVERLAP_CHARACTERS:]}\n\n{paragraph}"
    if current:
        chunks.append(current)
    return chunks


def _split_long_paragraph(paragraph: str) -> list[str]:
    chunks: list[str] = []
    start = 0
    while start < len(paragraph):
        end = min(start + MAX_CHUNK_CHARACTERS, len(paragraph))
        chunks.append(paragraph[start:end])
        start = end - CHUNK_OVERLAP_CHARACTERS if end < len(paragraph) else end
    return chunks


def checksum(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def index_documents(conn: Any, documents: Iterable[KnowledgeDocument], embedder: Embedder) -> None:
    """Upsert documents and fully replace their deterministic chunks when changed."""
    for document in documents:
        document_checksum = checksum(document.content)
        existing = conn.execute("SELECT checksum FROM documents WHERE id = %s", (document.id,)).fetchone()
        if existing is not None and existing[0] == document_checksum:
            continue
        conn.execute(
            """
            INSERT INTO documents (id, title, subject, document_date, source, tags, checksum, content)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET title = EXCLUDED.title, subject = EXCLUDED.subject,
                document_date = EXCLUDED.document_date, source = EXCLUDED.source, tags = EXCLUDED.tags,
                checksum = EXCLUDED.checksum, content = EXCLUDED.content, updated_at = NOW()
            """,
            (document.id, document.title, document.subject, document.date, document.source, document.tags, document_checksum, document.content),
        )
        conn.execute("DELETE FROM document_chunks WHERE document_id = %s", (document.id,))
        chunks = chunk_text(document.content)
        embeddings = embedder.embed(chunks)
        for index, (content, embedding) in enumerate(zip(chunks, embeddings, strict=True)):
            conn.execute(
                "INSERT INTO document_chunks (document_id, chunk_index, content, checksum, embedding) VALUES (%s, %s, %s, %s, %s::vector)",
                (document.id, index, content, checksum(content), json.dumps(embedding)),
            )
    conn.commit()


def retrieve(conn: Any, question: str, embedder: Embedder, *, limit: int = 5) -> list[RetrievedChunk]:
    """Run exact pgvector cosine search; this corpus is intentionally tiny."""
    vector = json.dumps(embedder.embed([question])[0])
    rows = conn.execute(
        """
        SELECT c.id, c.document_id, c.content, 1 - (c.embedding <=> %s::vector) AS similarity
        FROM document_chunks AS c
        WHERE c.embedding IS NOT NULL
        ORDER BY c.embedding <=> %s::vector
        LIMIT %s
        """,
        (vector, vector, limit),
    ).fetchall()
    return [RetrievedChunk(str(row[0]), str(row[1]), str(row[2]), float(row[3])) for row in rows]
