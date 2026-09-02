"""Production OpenAI adapters kept behind the RAG protocols."""

from collections.abc import Sequence
from typing import Any

from openai import OpenAI

from basketball_api.rag import RetrievedChunk


class OpenAIEmbedder:
    def __init__(self, api_key: str, model: str) -> None:
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        response = self.client.embeddings.create(model=self.model, input=list(texts))
        return [item.embedding for item in response.data]


class OpenAIGenerator:
    def __init__(self, api_key: str, model: str) -> None:
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def generate(
        self, question: str, statistics: dict[str, Any], evidence: Sequence[RetrievedChunk]
    ) -> str:
        evidence_text = "\n\n".join(
            f"[evidence:{item.evidence_id}] {item.content}" for item in evidence
        )
        response = self.client.responses.create(
            model=self.model,
            store=False,
            instructions=(
                "Answer only from supplied statistics and evidence. Cite evidence IDs in square "
                "brackets. State data limitations when evidence does not establish the claim."
            ),
            input=f"Question: {question}\nStatistics: {statistics}\nEvidence:\n{evidence_text}",
        )
        return response.output_text
