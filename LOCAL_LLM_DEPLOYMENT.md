# Local LLM Deployment Guide

This project is deployment-ready for a local-first document generation setup with Ollama as the default LLM provider. Keep `LLM_PROVIDER=ollama` for offline/private deployments.

## Recommended Models

Use these Ollama models for the best balance of document quality, structured JSON output, and local hardware requirements.

| Purpose | Model | When to use |
| --- | --- | --- |
| Best default generation | `qwen2.5:7b-instruct` | Strong structured output and good CPU/GPU compatibility |
| Higher-quality generation | `qwen2.5:14b-instruct` | Use on 16 GB+ VRAM or a strong workstation |
| Alternative generation | `llama3.1:8b-instruct` | Good prose quality; benchmark JSON reliability against Qwen |
| Fast lightweight generation | `mistral:7b-instruct` | Use when latency matters more than rich detail |
| Enterprise-grade generation | `llama3.1:70b-instruct` | Use only with high-memory GPU infrastructure |
| Default embeddings | `nomic-embed-text` | Fast, reliable retrieval for requirements and training docs |
| Stronger embeddings | `mxbai-embed-large` | Better semantic matching when you can spend more memory/time |
| Lightweight embeddings | `bge-small-en-v1.5` | Good for smaller machines or larger corpora |

## Local Docker Deployment

Start the application stack:

```bash
docker compose up --build
```

In another terminal, pull the recommended models into the Ollama container:

```bash
docker compose exec ollama ollama pull qwen2.5:7b-instruct
docker compose exec ollama ollama pull nomic-embed-text
```

Open:

- Frontend: http://localhost:5173
- API: http://localhost:8000/docs
- Health: http://localhost:8000/health

The health response should show:

```json
{
  "llm_provider": "ollama",
  "generation_model": "qwen2.5:7b-instruct",
  "embedding_model": "nomic-embed-text",
  "ollama_reachable": true
}
```

## Production Settings

For a server or Kubernetes deployment, set:

```env
ENVIRONMENT=production
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST:5432/DB
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://PRIVATE_OLLAMA_HOST:11434
OLLAMA_GENERATION_MODEL=qwen2.5:14b-instruct
OLLAMA_EMBED_MODEL=nomic-embed-text
JWT_SECRET_KEY=<strong-random-secret>
ALLOWED_ORIGINS=https://your-frontend-domain
VITE_API_BASE_URL=https://your-api-domain
```

Leave `GROQ_API_KEY` empty for private local-LLM deployments. Set `LLM_PROVIDER=groq` only when you intentionally want cloud generation.

## Training Modes

For testing, keep training fast and stable:

```env
TRAINING_USE_LLM_NORMALIZATION=false
TRAINING_EMBED_ON_UPLOAD=false
TRAINING_MAX_CHUNKS_PER_DOCUMENT=40
```

This stores chunked training knowledge immediately and avoids long Ollama calls during upload. It is the best mode for UI testing and demo data loading.

For better retrieval quality after the flow is stable, enable embeddings on a stronger machine:

```env
TRAINING_EMBED_ON_UPLOAD=true
OLLAMA_EMBED_MODEL=nomic-embed-text
OLLAMA_EMBED_TIMEOUT_SECONDS=10
```

Enable `TRAINING_USE_LLM_NORMALIZATION=true` only for small batches or background jobs. It calls the generation model during upload and can make large PDFs slow.

## Deployment Notes

- Keep Ollama close to the API server on the same host or private network; generation calls can run for several minutes.
- Use Postgres for multi-user deployments.
- Mount persistent storage for `app/storage` so uploaded requirements, training files, and exports survive restarts.
- Build the frontend with the final API URL because Vite embeds `VITE_API_BASE_URL` at build time.
- Rotate the default `JWT_SECRET_KEY` and replace demo accounts before exposing the app outside a trusted network.
