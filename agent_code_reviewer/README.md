# CodeSentinel 🛡️

**AI-Powered Security Vulnerability Scanner & Remediation Engine**

CodeSentinel scans your source code repositories for security vulnerabilities using a hybrid **AST + Regex** analysis engine, then generates secure fixes using local LLMs via [Ollama](https://ollama.ai).

---

## ✨ Features

- **Hybrid Scanning Engine** — Tree-sitter AST analysis for Python, JavaScript, and Java; regex fallback for other languages
- **13+ Vulnerability Patterns** — Detects code injection, command injection, SQL injection, XSS, hardcoded credentials, unsafe deserialization, and more
- **AI-Powered Remediation** — Generates secure code fixes with rationale and confidence scores using local LLMs (qwen3, mistral, llama3, etc.)
- **Interactive Diff Viewer** — Side-by-side comparison of vulnerable vs. fixed code
- **Multi-Language Support** — Scans `.py`, `.js`, `.ts`, `.java`, `.go`, `.c`, `.cpp`, `.php`, `.rb` files
- **Export Reports** — Download full vulnerability reports and individual fix patches as Markdown

---

## 🏗️ Architecture

```
agent_code_reviewer/
├── app.py                  # Streamlit UI — main entry point
├── agent/
│   ├── agent.py            # LLM integration via Ollama for fix generation
│   └── prompts.py          # Prompt templates for the LLM
├── core/
│   ├── parser.py           # Tree-sitter AST parsing & call-site extraction
│   ├── scanner.py          # Hybrid AST + regex vulnerability scanner
│   └── repo_loader.py      # Git repository cloning & file discovery
├── utils/
│   └── helpers.py          # Data models (RepoVulnerability)
├── test_scanner.py         # Pytest test suite
├── test_vuln.py            # Sample vulnerable file for testing
└── requirements.txt        # Python dependencies
```

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.9+**
- **Git**
- **[Ollama](https://ollama.ai)** installed and running locally with at least one model pulled:
  ```bash
  ollama pull qwen3
  ```

### Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd agent_code_reviewer

# Create a virtual environment (recommended)
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# Install dependencies
pip install -r requirements.txt
```

### Running the App

```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`.

### Running Tests

```bash
pytest test_scanner.py -v
```

---

## 🔍 How It Works

1. **Repository Loading** — Enter a GitHub URL or local path. CodeSentinel clones the repo and auto-detects file extensions.
2. **AST + Regex Scanning** — For Python/JS/Java, the tree-sitter AST parser extracts all function call sites and matches them against known dangerous functions (e.g., `eval`, `exec`, `os.system`). This avoids false positives from comments and strings. Regex patterns detect things AST can't (hardcoded creds, SQL injection, HTTP URLs).
3. **LLM Remediation** — Each vulnerability is sent to a local Ollama model, which generates a secure fix, a rationale explaining the risk, and a confidence score.
4. **Results Dashboard** — Vulnerabilities are displayed with severity badges, expandable details, inline explanations, diff viewers, and downloadable patches.

---

## 🛡️ Detected Vulnerability Types

| Vulnerability | Severity | Detection |
|---|---|---|
| Code Injection (`eval`/`exec`) | 🔴 HIGH | AST |
| Command Injection (`os.system`, `subprocess`) | 🔴 HIGH | AST |
| SQL Injection (f-string queries) | 🔴 HIGH | Regex |
| XSS (`render_template_string`) | 🔴 HIGH | AST |
| Unsafe Deserialization (`pickle`) | 🔴 HIGH | AST |
| Hardcoded Credentials/API Keys/Secrets | 🔴 HIGH | Regex |
| YAML Injection (`yaml.load`) | 🟠 MEDIUM | AST |
| Dynamic Import (`__import__`) | 🟠 MEDIUM | AST |
| Insecure HTTP Connection | 🟠 MEDIUM | Regex |
| Assertion Bypass | 🟢 LOW | Regex |

---

## ⚙️ Configuration

- **LLM Model** — Select from qwen3, mistral, llama3, codellama, or phi3 in the sidebar
- **File Extensions** — Auto-detected per repository, or manually configured
- **Streamlit Theme** — Configured in `.streamlit/config.toml`

---

## 📄 License

MIT License
