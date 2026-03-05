#!/bin/sh
# Example: import sample.env into keychain, then push those values to GitHub Actions secrets.
# Set REPO to your GitHub repo (e.g. owner/myapp) or leave unset to use the current repo via gh.

set -e

DOMAIN="${ENVELOPER_DOMAIN:-mydomain}"
PROJECT="${ENVELOPER_PROJECT:-myproject}"
REPO="${REPO:-}"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SAMPLE_ENV="${SCRIPT_DIR}/../sample.env"

if [ ! -f "$SAMPLE_ENV" ]; then
  echo "Not found: $SAMPLE_ENV"
  exit 1
fi

echo "Importing from sample.env into keychain (domain=$DOMAIN, project=$PROJECT)..."
enveloper import "$SAMPLE_ENV" --domain "$DOMAIN" --project "$PROJECT"

if [ -z "$REPO" ]; then
  echo "Pushing to GitHub (current repo)..."
  enveloper push --service github --domain "$DOMAIN" --project "$PROJECT"
else
  echo "Pushing to GitHub repo: $REPO"
  enveloper push --service github --repo "$REPO" --domain "$DOMAIN" --project "$PROJECT"
fi

echo "Done. Use secrets.MY_API_KEY, secrets.LEVEL_SET, etc. in your GitHub Actions workflow."
