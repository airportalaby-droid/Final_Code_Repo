# Static Analysis Engine Workflow Diagram

```mermaid
graph TD
    A[Receive structured code input (file paths from Member 1)] --> B[Parse code with Tree-sitter AST for Python/JS/Java]
    B --> C[Extract function call sites (eval, os.system, etc.)]
    C --> D[Match against dangerous call patterns]
    D --> E[Regex scanning for SQL injection, hardcoded secrets, etc.]
    E --> F[Detect vulnerabilities: Code Injection, XSS, Command Injection, etc.]
    F --> G[Generate RepoVulnerability objects with metadata]
    G --> H[Return structured JSON output: file_path, line_number, code_snippet, type, severity]
    H --> I[Member 1 formats and displays to user]
```

## How to view the diagram
- Copy the Mermaid code above
- Paste into any Mermaid viewer (e.g., GitHub, online editors)
- Or use VS Code with Mermaid extension