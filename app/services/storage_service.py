from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from app.core.config import settings


class StorageService:
    def __init__(self) -> None:
        self.requirement_dir = Path(settings.requirement_dir)
        self.export_dir = Path(settings.export_dir)

    def save_requirement(self, filename: str, content: bytes) -> Path:
        suffix = Path(filename).suffix.lower() or ".txt"
        target = self.requirement_dir / f"{uuid4().hex}{suffix}"
        target.write_bytes(content)
        return target

    def save_design(self, title: str, content: str, status: str = "draft") -> Path:
        safe_title = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "-" for ch in title.lower()).strip("-")
        target = self.export_dir / f"{safe_title or 'design'}-{status}-{uuid4().hex[:8]}.md"
        target.write_text(content, encoding="utf-8")
        return target

    def design_stem(self, title: str, status: str) -> str:
        safe_title = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "-" for ch in title.lower()).strip("-")
        return f"{safe_title or 'design'}-{status}-{uuid4().hex[:8]}"
