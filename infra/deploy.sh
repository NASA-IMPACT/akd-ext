#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INFRA_DIR="$ROOT_DIR/infra"

if ! command -v cdk >/dev/null 2>&1; then
  echo "cdk CLI not found. Install it with: npm install -g aws-cdk"
  exit 1
fi

python3 -m venv "$INFRA_DIR/.venv"
# shellcheck disable=SC1091
source "$INFRA_DIR/.venv/bin/activate"

pip install --upgrade pip
pip install -r "$INFRA_DIR/requirements.txt"

cd "$INFRA_DIR"

if [ -f "$ROOT_DIR/.env" ]; then
  set -a
  # shellcheck disable=SC1091
  source "$ROOT_DIR/.env"
  set +a
fi

EXTRA_ARGS=()
QUALIFIER="${CDK_BOOTSTRAP_QUALIFIER:-hnb659fds}"

if [[ "$*" != *"openaiSecretName="* ]] && [[ "$*" != *"openaiApiKey="* ]]; then
  if [ -n "${OPENAI_API_KEY:-}" ]; then
    EXTRA_ARGS+=(--context "openaiApiKey=${OPENAI_API_KEY}")
  fi
fi

EXTRA_ARGS+=(--context "@aws-cdk/core:bootstrapQualifier=${QUALIFIER}")

if [ "${SKIP_BOOTSTRAP:-0}" = "1" ]; then
  echo "Skipping CDK bootstrap (SKIP_BOOTSTRAP=1)"
else
  cdk bootstrap --qualifier "${QUALIFIER}"
fi

cdk deploy --require-approval never "$@" "${EXTRA_ARGS[@]}"
