#!/bin/sh
# Pull secrets from AWS (or skip if not configured), then export into env and run the main command.
# No .env file is used; variables come from enveloper (keychain/cloud).

set -e

if [ -n "${AWS_ACCESS_KEY_ID}" ] || [ -n "${AWS_SESSION_TOKEN}" ]; then
  enveloper pull --service aws --domain "${ENVELOPER_DOMAIN:-mydomain}" --project "${ENVELOPER_PROJECT:-myproject}" 2>/dev/null || true
fi

eval "$(enveloper --domain "${ENVELOPER_DOMAIN:-mydomain}" --project "${ENVELOPER_PROJECT:-myproject}" export --format unix 2>/dev/null)" || true

exec "$@"
