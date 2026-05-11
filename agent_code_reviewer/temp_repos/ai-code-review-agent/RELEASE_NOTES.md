# Release: AST Static Analysis Engine — Review Snapshot

Date: 2026-04-14

Summary
- Completed: core Python prototype for static analysis detecting SQL Injection, XSS, and hardcoded secrets.
- Includes: parser, detectors, LLM fallback, demo runner, unit tests, and CI workflow.

How to run demo locally
1. (Optional) Build tree-sitter bundle for precise JS/HTML parsing — see `TREE_SITTER_SETUP.md`.
2. Install requirements:
   ```bash
   python -m pip install -r requirements.txt
   ```
3. Run demo:
   ```bash
   python demo_runner.py
   ```
4. Run tests:
   ```bash
   pytest -q
   ```

What I validated
- `demo_runner.py` ran and produced vulnerability JSON from `samples/`.
- Unit tests in `tests/` passed on a machine without tree-sitter.

Known limitations
- Tree-sitter integration requires a compiled language bundle (`build/my-languages.so`) — see `TREE_SITTER_SETUP.md`.
- LLM integration uses a fallback template unless `OLLAMA_URL` is configured.

Files included in the review bundle
- `src/` — core modules (`parser.py`, `detectors.py`, `llm.py`, `engine.py`, etc.)
- `tests/` — simple unit scripts
- `demo_runner.py` and `samples/`
- `pytest.ini`, `requirements.txt`, `.github/workflows/ci.yml`
- `TREE_SITTER_SETUP.md` and `scripts/` helpers

Suggested talking points for review
- Detection strategy: Python AST-based SQLi heuristics, regex fallbacks, optional tree-sitter for JS/HTML.
- False-positive mitigation: parameterized query detection, assignment resolution.
- Next steps: expand AST queries, LangChain orchestration, integrate real LLM with prompt engineering, add more tests and CI coverage.
