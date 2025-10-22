#!/usr/bin/env bash
set -euo pipefail

# 内网构建辅助脚本：使用 .env 中的镜像参数构建镜像
# 变量：PIP_INDEX_URL, PIP_TRUSTED_HOST, DEBIAN_MIRROR, DEBIAN_SECURITY_MIRROR, DNF_MIRROR_CONF

echo "[build] using env:"
echo "  PIP_INDEX_URL=${PIP_INDEX_URL:-}"
echo "  PIP_TRUSTED_HOST=${PIP_TRUSTED_HOST:-}"
echo "  DEBIAN_MIRROR=${DEBIAN_MIRROR:-}"
echo "  DEBIAN_SECURITY_MIRROR=${DEBIAN_SECURITY_MIRROR:-}"
echo "  DNF_MIRROR_CONF=${#DNF_MIRROR_CONF:-0} chars"

echo "[build] building django, flower, site_worker via docker compose..."
docker compose build --no-cache --progress=plain django flower site_worker

if [[ "${BUILD_COMPUTE_WORKER:-0}" == "1" ]]; then
  echo "[build] building compute_worker image (Dockerfile.compute_worker)..."
  docker build \
    -f Dockerfile.compute_worker \
    --build-arg PIP_INDEX_URL="${PIP_INDEX_URL:-}" \
    --build-arg PIP_TRUSTED_HOST="${PIP_TRUSTED_HOST:-}" \
    --build-arg DNF_MIRROR_CONF="${DNF_MIRROR_CONF:-}" \
    --build-arg INSTALL_DOCKER="${INSTALL_DOCKER:-false}" \
    --no-cache --progress=plain \
    -t codabench/compute_worker:intranet .
fi

echo "[done] builds completed."

