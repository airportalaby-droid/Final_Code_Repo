Autonomous Code Review Agent (Static Analysis Engine)

Overview
- Simple prototype implementing AST/heuristic-based detectors for SQL Injection, XSS, and hardcoded secrets.
- Streamlit UI to scan a GitHub repo (clone or local path) and present findings.

Quickstart
1. Create a venv and install deps:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

2. Run UI:

```bash
streamlit run app.py
```

Notes
- The LLM integration uses a local Ollama-style endpoint if available (configure OLLAMA_URL). Otherwise, the system provides templated fix suggestions.
- This is a focused static analysis engine scaffold — extend detectors and tuning for your project.
