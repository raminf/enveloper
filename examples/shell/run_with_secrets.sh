#!/bin/sh
# Example: load env from enveloper (keychain or cloud), run a command, then unexport.
# No .env file is used. Domain/project can be overridden via ENVELOPER_DOMAIN / ENVELOPER_PROJECT.

set -e

DOMAIN="${ENVELOPER_DOMAIN:-mydomain}"
PROJECT="${ENVELOPER_PROJECT:-myproject}"

echo "Loading env from enveloper (domain=$DOMAIN, project=$PROJECT)..."
eval "$(enveloper --domain "$DOMAIN" --project "$PROJECT" export --format unix)"

echo "Env loaded. MY_API_KEY length=${#MY_API_KEY} LEVEL_SET=$LEVEL_SET"
# Run your app here, e.g.:
#   python app.py
#   make build
echo "Demo: running with secrets (no .env)."

echo "Clearing env..."
eval "$(enveloper --domain "$DOMAIN" --project "$PROJECT" unexport --format unix)"
echo "Done. Env cleared."
