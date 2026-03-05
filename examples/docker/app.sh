#!/bin/sh
# Example app: print that env vars are set (masked). No .env file needed.

echo "Env from enveloper (no .env):"
[ -n "$MY_API_KEY" ]     && echo "  MY_API_KEY is set (length ${#MY_API_KEY})"
[ -n "$MY_API_SECRET" ]  && echo "  MY_API_SECRET is set (length ${#MY_API_SECRET})"
[ -n "$LEVEL_SET" ]      && echo "  LEVEL_SET=$LEVEL_SET"
echo "Done."
