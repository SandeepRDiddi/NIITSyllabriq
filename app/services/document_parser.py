from __future__ import annotations

import json
import re
from pathlib import Path

from docx import Document
from pypdf import PdfReader

from app.services.text_utils import dedupe_keep_order, normalize_whitespace, split_sentences

_MIN_MODULE_NAME_LEN = 10

# Metadata-only sentence patterns produced by inline numbered lists — skip these
# when building functional_requirements (e.g. "Modules: 1", "Title: ...", etc.)
_METADATA_SENTENCE_RE = re.compile(
    r"^(title|modules?|total\s+duration|customer|program\s+overview)\s*:",
    re.IGNORECASE,
)


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

        # Extract numbered module items first — these are the authoritative scope
        module_items = self._extract_numbered_modules(raw_text)

        # Scope: prefer explicit module names; fall back to keyword-matching lines that
        # are long enough to be real content (skip short headers like "Modules:")
        scope = dedupe_keep_order(
            module_items
            or [
                line for line in lines
                if any(key in line.lower() for key in ("scope", "module", "feature"))
                and len(line) > _MIN_MODULE_NAME_LEN
            ]
        )

        non_functional = dedupe_keep_order(
            [line for line in lines if any(key in line.lower() for key in ("performance", "security", "availability", "latency", "audit"))]
        )
        integrations = dedupe_keep_order([line for line in lines if "integrat" in line.lower() or "api" in line.lower()])
        constraints = dedupe_keep_order([line for line in lines if any(key in line.lower() for key in ("constraint", "must", "shall", "limit"))])
        assumptions = dedupe_keep_order([line for line in lines if "assum" in line.lower()])
        risks = dedupe_keep_order([line for line in lines if "risk" in line.lower()])

        # Functional requirements: prefer real bullets, then extracted modules,
        # then sentences — filtering out metadata fragments from inline numbered lists
        candidate_sentences = [s for s in sentences[:8] if not _METADATA_SENTENCE_RE.match(s)]
        functional = dedupe_keep_order(bullets or module_items or candidate_sentences)

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

    def _extract_numbered_modules(self, text: str) -> list[str]:
        """
        Extract numbered module items from requirement text, handling two formats:

          Multi-line:  "1. Cloud Computing (4 hrs)\n2. Docker (4 hrs)"
          Inline:      "Modules: 1. Cloud Computing (4 hrs) 2. Docker (4 hrs) ..."

        Returns clean module names without leading numbers or trailing index artefacts.
        """
        modules: list[str] = []

        # Pass 1 — per-line: match lines starting with "N." or "N)"
        for line in text.splitlines():
            stripped = line.strip()
            m = re.match(r"^\d+[\.\)]\s+(.{%d,})" % _MIN_MODULE_NAME_LEN, stripped)
            if m:
                # Drop any trailing lone digit left by an adjacent inline number
                name = re.sub(r"\s+\d+$", "", m.group(1)).strip()
                modules.append(name)

        if modules:
            return dedupe_keep_order(modules)

        # Pass 2 — inline: a single line containing multiple "N. item" segments
        for line in text.splitlines():
            if len(re.findall(r"\d+\.", line)) >= 2:
                parts = re.split(r"(?<!\d)\d+\.\s+", line)
                for part in parts:
                    part = re.sub(r"\s+\d+$", "", part).strip()
                    if len(part) >= _MIN_MODULE_NAME_LEN:
                        modules.append(part)
                break

        return dedupe_keep_order(modules)

    def _extract_bullets(self, text: str) -> list[str]:
        bullets: list[str] = []
        for line in text.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            # Only treat "-" and "*" prefixed lines as bullets.
            # Numbered lines are handled by _extract_numbered_modules instead.
            if stripped.startswith(("-", "*")):
                bullets.append(stripped.lstrip("-* ").strip())
        return dedupe_keep_order(bullets)

