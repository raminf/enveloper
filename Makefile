.PHONY: help install dev test test-cov lint format build publish publish-test bump-patch bump-minor bump-major clean

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

format: ## Auto-format code with ruff
	uv run ruff format src/ tests/

build: ## Build sdist and wheel
	uv build

publish-test: build ## Publish to TestPyPI
	uv publish --index-url https://test.pypi.org/legacy/

publish: build ## Publish to PyPI
	uv publish

bump-patch: ## Bump patch version (0.1.0 -> 0.1.1)
	@python3 scripts/bump_version.py patch
	@echo "Version bumped to $$(python3 -c "import tomllib; print(tomllib.load(open('pyproject.toml','rb'))['project']['version'])")"

bump-minor: ## Bump minor version (0.1.0 -> 0.2.0)
	@python3 scripts/bump_version.py minor
	@echo "Version bumped to $$(python3 -c "import tomllib; print(tomllib.load(open('pyproject.toml','rb'))['project']['version'])")"

bump-major: ## Bump major version (0.1.0 -> 1.0.0)
	@python3 scripts/bump_version.py major
	@echo "Version bumped to $$(python3 -c "import tomllib; print(tomllib.load(open('pyproject.toml','rb'))['project']['version'])")"

clean: ## Remove build artifacts
	rm -rf dist/ build/ *.egg-info src/*.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
