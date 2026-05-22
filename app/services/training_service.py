from __future__ import annotations

import json
import re

from sqlmodel import Session, select

from app.core.config import settings
from app.models.training import TrainingChunk, TrainingDocument
from app.services.document_parser import DocumentParser
from app.services.ollama_client import OllamaClient
from app.services.text_utils import normalize_whitespace, split_sentences


class TrainingService:
    def __init__(self) -> None:
        self.parser = DocumentParser()
        self.ollama = OllamaClient()

    def create_training_document(
        self,
        session: Session,
        title: str,
        source_filename: str,
        source_path: str,
        content_type: str,
        raw_text: str,
        uploaded_by: str,
    ) -> TrainingDocument:
        normalized = self._normalize(raw_text)
        summary = self._build_summary(normalized)
        training_document = TrainingDocument(
            title=title,
            source_filename=source_filename,
            source_path=source_path,
            content_type=content_type,
            raw_text=raw_text,
            normalized_json=json.dumps(normalized, ensure_ascii=True, indent=2),
            summary=summary,
            uploaded_by=uploaded_by,
        )
        session.add(training_document)
        session.commit()
        session.refresh(training_document)
        self._index_training_chunks(session, training_document)
        return training_document

    def list_training_documents(self, session: Session) -> list[TrainingDocument]:
        return session.exec(select(TrainingDocument).order_by(TrainingDocument.created_at.desc())).all()

    def _normalize(self, raw_text: str) -> dict:
        """Use LLM when available, fall back to heuristic parser."""
        if settings.training_use_llm_normalization and self.ollama.is_reachable():
            result = self._normalize_with_llm(raw_text)
            if result:
                return result
        return self.parser.normalize_requirement(raw_text)

    def _normalize_with_llm(self, raw_text: str) -> dict | None:
        prompt = (
            "Analyze the following design or requirements document and extract structured information.\n"
            "Return ONLY valid JSON with these exact keys (all values must be strings or lists of strings):\n"
            "- business_goal: string — the primary objective or purpose of this document\n"
            "- scope: list of strings — modules, features, or systems in scope\n"
            "- functional_requirements: list of strings — specific functional capabilities described\n"
            "- non_functional_requirements: list of strings — performance, security, scalability requirements\n"
            "- assumptions: list of strings — stated assumptions\n"
            "- constraints: list of strings — technical or business constraints\n"
            "- integrations: list of strings — external systems, APIs, or platforms referenced\n"
            "- risks: list of strings — identified risks or challenges\n"
            "- key_design_patterns: list of strings — architecture or design patterns mentioned\n"
            "- source_summary: list of strings — top 5 key sentences that summarise this document\n\n"
            f"Document (first 4000 characters):\n{raw_text[:4000]}"
        )
        result = self.ollama.generate(
            prompt=prompt,
            system_prompt=(
                "You are an expert enterprise architect. Extract structured knowledge from design documents. "
                "Return only valid JSON — no explanation, no markdown fences."
            ),
        )
        if not result:
            return None
        try:
            # Strip any markdown fences the model may have added
            cleaned = re.sub(r"^```[a-z]*\n?", "", result.strip(), flags=re.MULTILINE)
            cleaned = re.sub(r"\n?```$", "", cleaned.strip())
            return json.loads(cleaned)
        except Exception:
            # Try to extract a JSON object if extra text surrounds it
            match = re.search(r"\{.*\}", result, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group())
                except Exception:
                    pass
        return None

    def _build_summary(self, normalized: dict) -> str:
        goal = str(normalized.get("business_goal", ""))
        patterns = normalized.get("key_design_patterns", [])
        extras = f" Key patterns: {', '.join(str(p) for p in patterns[:3])}." if patterns else ""
        return (goal + extras)[:500]

    def _index_training_chunks(self, session: Session, training_document: TrainingDocument) -> None:
        if not training_document.id:
            return
        chunks = self._chunk_text(
            training_document.raw_text,
            max_chars=settings.training_chunk_max_chars,
        )[: settings.training_max_chunks_per_document]
        for index, chunk in enumerate(chunks):
            embedding = self.ollama.embed(chunk) if settings.training_embed_on_upload else None
            session.add(
                TrainingChunk(
                    training_document_id=training_document.id,
                    chunk_index=index,
                    content=chunk,
                    embedding_json=json.dumps(embedding) if embedding else None,
                )
            )
        session.commit()

    def _chunk_text(self, raw_text: str, max_chars: int = 1800, overlap_sentences: int = 2) -> list[str]:
        sentences = split_sentences(raw_text)
        if not sentences:
            normalized = normalize_whitespace(raw_text)
            return [normalized] if normalized else []

        chunks: list[str] = []
        current: list[str] = []
        current_len = 0
        for sentence in sentences:
            sentence_len = len(sentence) + 1
            if current and current_len + sentence_len > max_chars:
                chunks.append(" ".join(current))
                current = current[-overlap_sentences:] if overlap_sentences else []
                current_len = sum(len(item) + 1 for item in current)
            current.append(sentence)
            current_len += sentence_len

        if current:
            chunks.append(" ".join(current))
        return chunks
