# LLM and AI assistant guide

This page is for **maintainers** and for **LLMs (large language models)** or AI assistants that work on the enveloper repository. It points to the information they need to accomplish tasks correctly.

## Where to look

All LLM-oriented material lives in the **`LLM/`** directory at the repository root:

- **[LLM/README.md](../LLM/README.md)** — Entry point for an LLM: what enveloper is, repo layout, commands to run (`make check`, `uv run pytest`, etc.), and links to detailed guidelines.
- **LLM/guidelines/** — Detailed guidelines in separate documents:
  - [conventions.md](../LLM/guidelines/conventions.md) — Package manager (uv), Python version, project/domain semantics, code style.
  - [testing.md](../LLM/guidelines/testing.md) — How to run tests, pytest markers (unit/integration), fixtures, adding tests.
  - [examples.md](../LLM/guidelines/examples.md) — How examples are structured and how to add or change them.

If you are an LLM or an AI assistant working on this repo, read **LLM/README.md** first, then the guidelines as needed for the task.

## Tests for the LLM folder

The project includes tests that validate the **LLM/** structure and content so that required files and sections remain present. Run them with:

```bash
uv run pytest tests/test_llm.py -v
```

These tests are part of the normal test suite (`make test`).

## MCP server (for other LLMs to read env vars)

Enveloper can run an **MCP server** so that other LLMs (e.g. in Cursor or Claude Desktop) can read environment variables from this project’s keychain or cloud stores. See [MCP server](mcp.md) for install, tools, and client configuration. LLM-specific notes are in [LLM/guidelines/mcp.md](../LLM/guidelines/mcp.md).
