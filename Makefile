VERSION := $(shell grep '^version = ' pyproject.toml | sed 's/.*"\([^"]*\)".*/\1/')

.PHONY: help install dev test test-cov lint typecheck check format build publish publish-test bump-patch bump-minor bump-major release release-pypi release-test clean

help: ## Show this help
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-18s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install for development (editable, all extras)
	uv pip install -e ".[aws,dev]"

dev: ## Create venv, sync deps, install editable
	uv sync --all-extras

test: ## Run tests
	uv run pytest tests/ -v

test-cov: ## Run tests with coverage
	uv run pytest tests/ -v --cov=enveloper --cov-report=term-missing

lint: ## Run ruff linter
	uv run ruff check src/ tests/

typecheck: ## Run mypy type-checker (package + tests)
	uv run mypy -p enveloper && uv run mypy tests/

check: lint typecheck test ## Run lint, typecheck, and tests (CI gate)

build: ## Build sdist and wheel
	uv build

publish-test: bump-patch ## Bump patch version, then publish to TestPyPI (uses ~/.pypirc).
	rm -rf dist
	uv build
	uv run twine upload -r testpypi dist/*

publish: build ## Publish to PyPI (uses ~/.pypirc [pypi])
	uv run twine upload dist/*

bump-patch: ## Bump patch version (0.1.0 -> 0.1.1)
	@uv run python scripts/bump_version.py patch
	@echo "Version bumped to $$(grep '^version = ' pyproject.toml | sed 's/.*"\([^"]*\)".*/\1/')"

bump-minor: ## Bump minor version (0.1.0 -> 0.2.0)
	@uv run python scripts/bump_version.py minor
	@echo "Version bumped to $$(grep '^version = ' pyproject.toml | sed 's/.*"\([^"]*\)".*/\1/')"

bump-major: ## Bump major version (0.1.0 -> 1.0.0)
	@uv run python scripts/bump_version.py major
	@echo "Version bumped to $$(grep '^version = ' pyproject.toml | sed 's/.*"\([^"]*\)".*/\1/')"

release-pypi: ## Push to GitHub, create tag v$(VERSION), push tag → GitHub Actions publishes to PyPI (bump + commit first)
	@test -z "$$(git status --porcelain)" || (echo "Uncommitted changes; commit or stash first."; exit 1)
	git push origin $$(git branch --show-current)
	git tag v$(VERSION)
	git push origin v$(VERSION)
	@echo "Tag v$(VERSION) pushed; GitHub Actions will publish to PyPI."

release-test: ## Push to GitHub, then trigger workflow to publish to TestPyPI (requires gh CLI; bump + commit first)
	@command -v gh >/dev/null 2>&1 || (echo "Need gh CLI: https://cli.github.com/"; exit 1)
	git push origin $$(git branch --show-current)
	gh workflow run publish.yml -f target=testpypi --ref $$(git branch --show-current)
	@echo "Pushed and triggered TestPyPI publish; see Actions tab."

release: release-pypi ## Alias for release-pypi

clean: ## Remove build artifacts
	rm -rf dist/ build/ *.egg-info src/*.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
