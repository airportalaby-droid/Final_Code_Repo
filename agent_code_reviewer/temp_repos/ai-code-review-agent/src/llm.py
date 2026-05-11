import os
from typing import Dict

OLLAMA_URL = os.getenv('OLLAMA_URL', '').rstrip('/')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'mistral')


def suggest_fix_with_llm(issue: Dict, context: str) -> Dict:
    """Return a suggestion dict with text and confidence. If Ollama URL configured, call it; otherwise produce a templated suggestion."""
    prompt = f"Issue: {issue['type']}\nMessage: {issue['message']}\nSnippet: {issue.get('snippet','')}\nProvide a concise fix suggestion and estimated confidence (0-1)."

    if OLLAMA_URL:
        try:
            try:
                import requests
            except Exception:
                raise

            resp = requests.post(
                f"{OLLAMA_URL}/api/generate",
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": prompt,
                    "max_tokens": 300
                },
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
            text = data.get('text') or data.get('output') or data.get('response') or str(data)
            return {"text": text, "confidence": issue.get('confidence', 0.6)}
        except Exception:
            pass

    # Fallback templated suggestions
    t = issue['type']
    if t == 'SQL Injection':
        text = 'Use parameterized queries / prepared statements. Pass user inputs as parameters to DB driver instead of string building.'
    elif t == 'XSS':
        text = 'Escape or sanitize user input and avoid innerHTML; use safe templating or textContent.'
    elif t == 'Hardcoded Secret':
        text = 'Remove the secret from source, store in env vars or a secret manager, and rotate compromised keys.'
    else:
        text = 'Review the code and avoid untrusted input in sensitive sinks.'

    return {"text": text, "confidence": issue.get('confidence', 0.6)}
