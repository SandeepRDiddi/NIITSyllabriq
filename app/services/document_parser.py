from __future__ import annotations

import json
from pathlib import Path

from docx import Document
from pypdf import PdfReader

from app.services.text_utils import dedupe_keep_order, normalize_whitespace, split_sentences


class DocumentParser:
    def extract_text(self, path: Path) -> str:
        suffix = path.suffix.lower()
        if suffix in {".txt", ".md"}:
            return path.read_text(encoding="utf-8")
        if suffix == ".docx":
            document = Document(str(path))
            return "\n".join(paragraph.text for paragraph in document.paragraphs)
        if suffix == ".pdf":
            reader = PdfReader(str(path))
            return "\n".join(page.extract_text() or "" for page in reader.pages)
        raise ValueError(f"Unsupported file type: {suffix}")

    def normalize_requirement(self, raw_text: str) -> dict[str, object]:
        text = normalize_whitespace(raw_text)
        sentences = split_sentences(text)
        bullets = self._extract_bullets(raw_text)
        lines = [line.strip("-* 0123456789.") for line in raw_text.splitlines() if line.strip()]

        scope = dedupe_keep_order([line for line in lines if any(key in line.lower() for key in ("scope", "module", "feature"))])
        non_functional = dedupe_keep_order(
            [line for line in lines if any(key in line.lower() for key in ("performance", "security", "availability", "latency", "audit"))]
        )
        integrations = dedupe_keep_order([line for line in lines if "integrat" in line.lower() or "api" in line.lower()])
        constraints = dedupe_keep_order([line for line in lines if any(key in line.lower() for key in ("constraint", "must", "shall", "limit"))])
        assumptions = dedupe_keep_order([line for line in lines if "assum" in line.lower()])
        risks = dedupe_keep_order([line for line in lines if "risk" in line.lower()])
        functional = dedupe_keep_order(bullets or sentences[:8])

        return {
            "business_goal": sentences[0] if sentences else text[:250],
            "scope": scope or functional[:3],
            "functional_requirements": functional,
            "non_functional_requirements": non_functional,
            "assumptions": assumptions,
            "constraints": constraints,
            "integrations": integrations,
            "risks": risks,
            "source_summary": sentences[:10],
        }

    def normalize_to_json(self, raw_text: str) -> str:
        return json.dumps(self.normalize_requirement(raw_text), indent=2, ensure_ascii=True)

    def _extract_bullets(self, text: str) -> list[str]:
        bullets: list[str] = []
        for line in text.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.startswith(("-", "*")) or stripped[:2].isdigit():
                bullets.append(stripped.lstrip("-* ").strip())
        return dedupe_keep_order(bullets)

