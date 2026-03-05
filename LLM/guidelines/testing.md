# Testing guidelines for LLMs

How tests are organized and how to run or add them.

## Running tests

- **All tests:** `uv run pytest tests/ -v` or `make test`
- **With coverage:** `uv run pytest tests/ -v --cov=enveloper --cov-report=term-missing` or `make test-cov`
- **Example tests only:** `uv run pytest tests/test_examples.py -v`
- **Unit (examples) only:** `uv run pytest tests/test_examples.py -m unit`
- **Integration (examples) only:** `uv run pytest tests/test_examples.py -m integration`
- **LLM structure/content tests:** `uv run pytest tests/test_llm.py -v`

## Test layout

- **`tests/conftest.py`** — Shared fixtures: `cli_runner`, `mock_keyring`, `sample_env`, and autouse mocks so unit tests do not touch the real keychain or cloud. Integration tests can use the same fixtures when running in-process.
- **`tests/test_examples.py`** — Structure, content, and runnable checks for the **examples/** folder (unit and integration markers).
- **`tests/test_llm.py`** — Checks that the **LLM/** folder and required guideline files exist and contain expected sections.
- Other **`tests/test_*.py`** — Module-specific tests (CLI, store, SDK, config, etc.).

## Markers (pytest)

Defined in `pyproject.toml`:

- **`@pytest.mark.unit`** — Unit tests: structure, content, in-process CLI with mocks. No subprocess or real backends.
- **`@pytest.mark.integration`** — Integration tests: subprocess scripts, full workflows (e.g. shell script with file store, import→export→unexport).
- **`integration_aws`**, **`integration_gcp`**, etc. — Optional markers for cloud-backed tests (require env vars and credentials); not used by the default `make check` unless explicitly run.

## Adding tests

- For **new example code**: Add corresponding tests in **`tests/test_examples.py`** (unit: file exists, content has expected strings; integration: run script with file store or in-process CLI where applicable).
- For **new LLM content**: Ensure **`tests/test_llm.py`** is updated if you add required files or sections (see that file for the contract).
- Use **`mock_keyring`** and **`sample_env`** (and optionally **`cli_runner`**) for in-process CLI/SDK tests so no real keychain is used.
- For subprocess tests (e.g. running a shell script), set **`ENVELOPER_SERVICE=file`** and a temp **`.env`** in `cwd` so the subprocess uses the file store and does not require keychain or cloud.
