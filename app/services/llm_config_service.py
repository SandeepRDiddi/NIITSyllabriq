from __future__ import annotations

from datetime import datetime

from sqlmodel import Session, select

from app.core.config import settings
from app.models.llm_config import LLMProviderConfig


DEFAULT_MODELS = {
    "ollama": settings.ollama_generation_model,
    "groq": settings.groq_model,
    "anthropic": settings.anthropic_model,
    "openai": settings.openai_model,
    "openai_compatible": "",
}


class LLMConfigService:
    def get_active_config(self, session: Session) -> LLMProviderConfig:
        config = session.exec(
            select(LLMProviderConfig)
            .where(LLMProviderConfig.is_active == True)  # noqa: E712
            .order_by(LLMProviderConfig.updated_at.desc())
        ).first()
        if config:
            return config
        return LLMProviderConfig(
            provider=settings.llm_provider.strip().lower() or "ollama",
            model=self._env_model(settings.llm_provider),
            api_key=self._env_api_key(settings.llm_provider),
            base_url=self._env_base_url(settings.llm_provider),
            is_active=True,
            updated_by="system",
        )

    def save_active_config(
        self,
        session: Session,
        provider: str,
        model: str,
        base_url: str,
        api_key: str | None,
        updated_by: str,
    ) -> LLMProviderConfig:
        provider_key = provider.strip().lower()
        existing = session.exec(select(LLMProviderConfig).where(LLMProviderConfig.is_active == True)).all()  # noqa: E712
        config = existing[0] if existing else LLMProviderConfig(is_active=True)
        for stale in existing[1:]:
            stale.is_active = False
            session.add(stale)

        config.provider = provider_key
        config.model = model.strip() or DEFAULT_MODELS.get(provider_key, "")
        config.base_url = base_url.strip()
        if api_key is not None and api_key.strip():
            config.api_key = api_key.strip()
        elif provider_key == "ollama":
            config.api_key = ""
        config.updated_by = updated_by
        config.updated_at = datetime.utcnow()
        session.add(config)
        session.commit()
        session.refresh(config)
        return config

    def _env_model(self, provider: str) -> str:
        provider_key = provider.strip().lower()
        return DEFAULT_MODELS.get(provider_key) or settings.ollama_generation_model

    def _env_api_key(self, provider: str) -> str:
        provider_key = provider.strip().lower()
        if provider_key == "groq":
            return settings.groq_api_key
        if provider_key == "anthropic":
            return settings.anthropic_api_key
        if provider_key == "openai":
            return settings.openai_api_key
        if provider_key == "openai_compatible":
            return settings.openai_compatible_api_key
        return ""

    def _env_base_url(self, provider: str) -> str:
        provider_key = provider.strip().lower()
        if provider_key == "ollama":
            return settings.ollama_base_url
        if provider_key == "openai_compatible":
            return settings.openai_compatible_base_url
        return ""


llm_config_service = LLMConfigService()
