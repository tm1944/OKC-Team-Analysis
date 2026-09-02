#!/usr/bin/env python
"""Embed committed knowledge documents into local pgvector tables."""

from pathlib import Path

import psycopg

from basketball_api.config import get_settings
from basketball_api.openai_clients import OpenAIEmbedder
from basketball_api.rag import index_documents, load_documents


def main() -> None:
    settings = get_settings()
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is required to index knowledge documents")
    with psycopg.connect(settings.database_url) as conn:
        index_documents(
            conn,
            load_documents(Path("documents")),
            OpenAIEmbedder(settings.openai_api_key, settings.openai_embedding_model),
        )
    print("Knowledge documents indexed")


if __name__ == "__main__":
    main()
