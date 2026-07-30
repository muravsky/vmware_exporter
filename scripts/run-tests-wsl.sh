#!/usr/bin/env bash
set -euo pipefail

# Optional corporate proxy for WSL. Set HTTP_PROXY/HTTPS_PROXY before running if needed.
if [[ -n "${HTTP_PROXY:-}" ]]; then
  export HTTPS_PROXY="${HTTPS_PROXY:-$HTTP_PROXY}"
  export http_proxy="${http_proxy:-$HTTP_PROXY}"
  export https_proxy="${https_proxy:-$HTTPS_PROXY}"
fi
export NO_PROXY="${NO_PROXY:-localhost,127.0.0.1}"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [[ -n "${HTTPS_PROXY:-}" ]]; then
  if ! curl -fsS --connect-timeout 5 --proxy "$HTTPS_PROXY" https://pypi.org/simple/pip/ >/dev/null; then
    echo "Cannot reach PyPI via proxy ($HTTPS_PROXY)." >&2
    echo "Check VPN, proxy host, and corporate CA setup in WSL." >&2
    exit 1
  fi
fi
python3 -m venv .venv-wsl
source .venv-wsl/bin/activate
pip install --upgrade pip setuptools wheel
pip install -e . -r requirements.txt -r requirements-tests.txt
pytest tests/unit -v "$@"
