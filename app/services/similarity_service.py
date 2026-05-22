from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Optional, Sequence

from sqlmodel import Session, select

from app.models.design import DesignDocument
from app.models.requirement import Requirement
from app.models.training import TrainingChunk, TrainingDocument
from app.services.ollama_client import OllamaClient
from app.services.text_utils import cosine_similarity, normalize_whitespace, top_matching_sentences


@dataclass
class SimilarityMatch:
    requirement_id: int
    design_id: int | None
    training_document_id: Optional[int]
    title: str
    source_type: str
    similarity_score: float
    reused_sections: list[str]


class SimilarityService:
    def __init__(self) -> None:
        self.ollama = OllamaClient()

    def find_matches(self, session: Session, requirement_text: str, top_k: int = 3) -> Sequence[SimilarityMatch]:
        requirements = session.exec(select(Requirement)).all()
        training_documents = session.exec(select(TrainingDocument).where(TrainingDocument.status == "ACTIVE")).all()
        training_by_id = {item.id: item for item in training_documents}
        training_chunks = session.exec(select(TrainingChunk)).all()
        designs = {design.requirement_id: design for design in session.exec(select(DesignDocument)).all()}
        query_text = normalize_whitespace(requirement_text)

        query_embedding = self.ollama.embed(query_text)
        scored: list[SimilarityMatch] = []
        for req in requirements:
            candidate_text = normalize_whitespace(req.raw_text)
            lexical_score = cosine_similarity(query_text, candidate_text)
            semantic_score = lexical_score

            if query_embedding:
                candidate_embedding = self.ollama.embed(candidate_text)
                if candidate_embedding:
                    semantic_score = self._vector_cosine(query_embedding, candidate_embedding)

            score = max(lexical_score, semantic_score)
            design = designs.get(req.id)
            reused_sections = top_matching_sentences(query_text, candidate_text, limit=5)
            scored.append(
                SimilarityMatch(
                    requirement_id=req.id or 0,
                    design_id=design.id if design else None,
                    training_document_id=None,
                    title=req.title,
                    source_type="requirement",
                    similarity_score=score,
                    reused_sections=reused_sections,
                )
            )

        if training_chunks:
            for chunk in training_chunks:
                doc = training_by_id.get(chunk.training_document_id)
                if not doc:
                    continue
                candidate_text = normalize_whitespace(chunk.content)
                lexical_score = cosine_similarity(query_text, candidate_text)
                semantic_score = lexical_score

                if query_embedding and chunk.embedding_json:
                    candidate_embedding = self._load_embedding(chunk.embedding_json)
                    if candidate_embedding:
                        semantic_score = self._vector_cosine(query_embedding, candidate_embedding)

                score = max(lexical_score, semantic_score)
                reused_sections = top_matching_sentences(query_text, candidate_text, limit=5)
                scored.append(
                    SimilarityMatch(
                        requirement_id=0,
                        design_id=None,
                        training_document_id=doc.id,
                        title=doc.title,
                        source_type="training_document",
                        similarity_score=score,
                        reused_sections=reused_sections or [candidate_text[:500]],
                    )
                )
        else:
            for doc in training_documents:
                candidate_text = normalize_whitespace(doc.raw_text)
                lexical_score = cosine_similarity(query_text, candidate_text)
                semantic_score = lexical_score

                if query_embedding:
                    candidate_embedding = self.ollama.embed(candidate_text)
                    if candidate_embedding:
                        semantic_score = self._vector_cosine(query_embedding, candidate_embedding)

                score = max(lexical_score, semantic_score)
                reused_sections = top_matching_sentences(query_text, candidate_text, limit=5)
                scored.append(
                    SimilarityMatch(
                        requirement_id=0,
                        design_id=None,
                        training_document_id=doc.id,
                        title=doc.title,
                        source_type="training_document",
                        similarity_score=score,
                        reused_sections=reused_sections,
                    )
                )

        scored.sort(key=lambda item: item.similarity_score, reverse=True)
        return scored[:top_k]

    def _load_embedding(self, embedding_json: str) -> list[float] | None:
        try:
            data = json.loads(embedding_json)
        except Exception:
            return None
        if isinstance(data, list) and all(isinstance(item, (int, float)) for item in data):
            return [float(item) for item in data]
        return None

    def _vector_cosine(self, vector_a: list[float], vector_b: list[float]) -> float:
        if not vector_a or not vector_b or len(vector_a) != len(vector_b):
            return 0.0
        dot = sum(a * b for a, b in zip(vector_a, vector_b))
        norm_a = sum(a * a for a in vector_a) ** 0.5
        norm_b = sum(b * b for b in vector_b) ** 0.5
        if not norm_a or not norm_b:
            return 0.0
        return dot / (norm_a * norm_b)
