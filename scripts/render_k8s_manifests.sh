#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
OUT_DIR="${ROOT_DIR}/k8s/rendered"

rm -rf "${OUT_DIR}"
mkdir -p "${OUT_DIR}"

for file in \
  "${ROOT_DIR}/k8s/base/configmap.yaml" \
  "${ROOT_DIR}/k8s/base/secret.template.yaml" \
  "${ROOT_DIR}/k8s/base/backend-deployment.yaml" \
  "${ROOT_DIR}/k8s/base/backend-service.yaml" \
  "${ROOT_DIR}/k8s/base/frontend-deployment.yaml" \
  "${ROOT_DIR}/k8s/base/frontend-service.yaml" \
  "${ROOT_DIR}/k8s/base/worker-deployment.yaml" \
  "${ROOT_DIR}/k8s/base/ingress.yaml" \
  "${ROOT_DIR}/k8s/base/hpa-api.yaml" \
  "${ROOT_DIR}/k8s/base/hpa-workers.yaml" \
  "${ROOT_DIR}/k8s/base/namespace.yaml"
do
  target="${OUT_DIR}/$(basename "${file}" .template)"
  sed \
    -e "s|__BACKEND_IMAGE__|${BACKEND_IMAGE}|g" \
    -e "s|__FRONTEND_IMAGE__|${FRONTEND_IMAGE}|g" \
    -e "s|__APP_HOST__|${APP_HOST}|g" \
    -e "s|__API_HOST__|${API_HOST}|g" \
    -e "s|__DATABASE_URL__|${DATABASE_URL}|g" \
    -e "s|__JWT_SECRET_KEY__|${JWT_SECRET_KEY}|g" \
    -e "s|__SPACES_ACCESS_KEY__|${SPACES_ACCESS_KEY}|g" \
    -e "s|__SPACES_SECRET_KEY__|${SPACES_SECRET_KEY}|g" \
    -e "s|__SPACES_ENDPOINT__|${SPACES_ENDPOINT}|g" \
    -e "s|__SPACES_BUCKET_TRAINING__|${SPACES_BUCKET_TRAINING}|g" \
    -e "s|__SPACES_BUCKET_REQUIREMENTS__|${SPACES_BUCKET_REQUIREMENTS}|g" \
    -e "s|__SPACES_BUCKET_EXPORTS__|${SPACES_BUCKET_EXPORTS}|g" \
    -e "s|__ALLOWED_ORIGINS__|${ALLOWED_ORIGINS}|g" \
    -e "s|__LLM_PROVIDER__|${LLM_PROVIDER:-ollama}|g" \
    -e "s|__OLLAMA_BASE_URL__|${OLLAMA_BASE_URL}|g" \
    -e "s|__OLLAMA_GENERATION_MODEL__|${OLLAMA_GENERATION_MODEL}|g" \
    -e "s|__OLLAMA_EMBED_MODEL__|${OLLAMA_EMBED_MODEL}|g" \
    "${file}" > "${target}"
done

echo "Rendered manifests to ${OUT_DIR}"
