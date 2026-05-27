from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "NIIT Design Automation"
    environment: str = "development"
    database_url: str = "sqlite:///./niit_design_automation.db"
    postgres_url: str = "postgresql+psycopg://niit:niit@localhost:5432/niit_design_automation"
    llm_provider: str = "ollama"
    ollama_base_url: str = "http://localhost:11434"
    ollama_generation_model: str = "qwen2.5:7b-instruct"
    ollama_embed_model: str = "nomic-embed-text"
    ollama_embed_timeout_seconds: float = 10.0
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-3-5-sonnet-latest"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    openai_compatible_api_key: str = ""
    openai_compatible_base_url: str = ""
    training_use_llm_normalization: bool = False
    training_embed_on_upload: bool = False
    training_chunk_max_chars: int = 1800
    training_max_chunks_per_document: int = 40
    similarity_threshold: float = 0.78
    primary_reviewers: str = Field(default="primary.reviewer@niit.com")
    final_reviewers: str = Field(default="final.reviewer1@niit.com,final.reviewer2@niit.com")
    export_dir: str = "app/storage/designs"
    requirement_dir: str = "app/storage/requirements"
    template_dir: str = "app/templates/designs"
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 480
    allowed_origins: str = "http://localhost:3000,http://localhost:5173,http://127.0.0.1:5173"

    @property
    def primary_reviewer_list(self) -> List[str]:
        return [item.strip() for item in self.primary_reviewers.split(",") if item.strip()]

    @property
    def final_reviewer_list(self) -> List[str]:
        return [item.strip() for item in self.final_reviewers.split(",") if item.strip()]

    @property
    def allowed_origin_list(self) -> List[str]:
        return [item.strip() for item in self.allowed_origins.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
