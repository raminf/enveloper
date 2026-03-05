# Makefile example: load env from enveloper (keychain or cloud), no .env file.
# Usage: make -f examples/makefile/Makefile demo
# Optional: make -f examples/makefile/Makefile unexport  (run in shell that ran demo)

DOMAIN ?= mydomain
PROJECT ?= myproject

.PHONY: demo unexport show-env

# Demo target: load secrets via export (unix), run a command, then unexport in the same recipe.
# In practice you might run "make demo" and later "make unexport" in the same shell.
demo:
	@echo "Loading env from enveloper (domain=$(DOMAIN), project=$(PROJECT))..."
	@eval "$$(enveloper --domain $(DOMAIN) --project $(PROJECT) export --format unix)" && \
		echo "MY_API_KEY length: $${#MY_API_KEY}" && \
		echo "LEVEL_SET=$$LEVEL_SET" && \
		echo "Demo done. Run 'make unexport' in this shell to clear env."

# Show that export populates env (run in subshell so vars don't persist in your shell)
show-env:
	@eval "$$(enveloper --domain $(DOMAIN) --project $(PROJECT) export --format unix)" && \
		env | grep -E '^(MY_API_|LEVEL_SET)' || true

# Unexport: run in the same shell where you ran a target that loaded env, to clear variables.
# Example: (eval "$$(enveloper export ...)"; make demo); make unexport
unexport:
	@eval "$$(enveloper --domain $(DOMAIN) --project $(PROJECT) unexport --format unix)" && \
		echo "Env vars unset."
