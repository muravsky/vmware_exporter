#!/usr/bin/env bash
set -euo pipefail

IMAGE="${IMAGE:-muravsky/vmware-exporter}"
TAG="${TAG:-dev-$(date +%Y%m%d)}"
PLATFORM="${PLATFORM:-}"
PUSH="${PUSH:-0}"

repo_root="$(cd "$(dirname "$0")/.." && pwd)"
cd "$repo_root"

full_tag="${IMAGE}:${TAG}"

echo "Building test image: ${full_tag}"

if [[ -n "${PLATFORM}" ]]; then
  if [[ "${PUSH}" == "1" ]]; then
    docker buildx build --platform "${PLATFORM}" -t "${full_tag}" --push .
  else
    docker buildx build --platform "${PLATFORM}" -t "${full_tag}" --load .
  fi
else
  docker build -t "${full_tag}" .
fi

if [[ "${PUSH}" != "1" ]]; then
  cat <<EOF

Built locally. Run side-by-side with production latest:
  docker run -d --name vmware_exporter_old -p 9272:9272 ... ${IMAGE}:latest
  docker run -d --name vmware_exporter_new -p 9273:9272 ... ${full_tag}

To push this test tag (without touching latest):
  PUSH=1 TAG=${TAG} ./scripts/docker-build-test.sh
EOF
  exit 0
fi

cat <<EOF

Pushed: ${full_tag}
Pull and run on another host:
  docker pull ${full_tag}
  docker run -d --name vmware_exporter_test -p 9273:9272 ... ${full_tag}
EOF
