#!/bin/sh
# Demo: domains, projects, and semver versioning.
# Sets keys under different domain/project/version, then lists and gets them.
# Uses local keychain; run from repo root so 'enveloper' is on PATH.

set -e

PROJECT="${ENVELOPER_PROJECT:-myapp}"

echo "=== Domains, projects, and versioning demo ==="
echo ""

# Use a dedicated domain for the demo so we don't clash with real data
DOMAIN="demo_dpv"

echo "1. Setting keys in domain=$DOMAIN, project=$PROJECT, versions 1.0.0 and 2.0.0"
enveloper set API_KEY "key-v1" -d "$DOMAIN" -p "$PROJECT" --version 1.0.0
enveloper set API_KEY "key-v2" -d "$DOMAIN" -p "$PROJECT" --version 2.0.0
enveloper set DB_URL "postgres://v1" -d "$DOMAIN" -p "$PROJECT" --version 1.0.0
enveloper set DB_URL "postgres://v2" -d "$DOMAIN" -p "$PROJECT" --version 2.0.0

echo ""
echo "2. Setting keys in same domain, different project (worker)"
enveloper set WORKER_QUEUE "queue-v1" -d "$DOMAIN" -p "worker" --version 1.0.0

echo ""
echo "3. List domains (should include $DOMAIN)"
enveloper list domain

echo ""
echo "4. List projects under domain $DOMAIN"
enveloper list project -d "$DOMAIN"

echo ""
echo "5. Get API_KEY for version 1.0.0 vs 2.0.0"
echo -n "   -d $DOMAIN -p $PROJECT --version 1.0.0: "
enveloper get API_KEY -d "$DOMAIN" -p "$PROJECT" --version 1.0.0
echo -n "   -d $DOMAIN -p $PROJECT --version 2.0.0: "
enveloper get API_KEY -d "$DOMAIN" -p "$PROJECT" --version 2.0.0

echo ""
echo "6. Export (unix) for domain=$DOMAIN project=$PROJECT version=2.0.0 (first 2 lines)"
enveloper export -d "$DOMAIN" -p "$PROJECT" --version 2.0.0 --format unix | head -2

echo ""
echo "=== Cleanup: delete demo keys (optional) ==="
echo "To remove the demo keys, run:"
echo "  enveloper delete API_KEY -d $DOMAIN -p $PROJECT --version 1.0.0"
echo "  enveloper delete API_KEY -d $DOMAIN -p $PROJECT --version 2.0.0"
echo "  enveloper delete DB_URL  -d $DOMAIN -p $PROJECT --version 1.0.0"
echo "  enveloper delete DB_URL  -d $DOMAIN -p $PROJECT --version 2.0.0"
echo "  enveloper delete WORKER_QUEUE -d $DOMAIN -p worker --version 1.0.0"
echo "Or: enveloper clear -d $DOMAIN -p $PROJECT"
echo ""
echo "Done."
