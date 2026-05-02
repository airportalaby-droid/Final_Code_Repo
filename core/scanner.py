import re
import os
from typing import List
from utils.helpers import RepoVulnerability
from core.parser import extract_call_sites, parser_available

# ── AST-based dangerous call patterns ────────────────────────────────────────
# Maps function names (or dotted paths) to (vulnerability_type, severity)
AST_DANGEROUS_CALLS = {
    "eval":               ("Code Injection (eval)", "HIGH"),
    "exec":               ("Code Injection (exec)", "HIGH"),
    "os.system":          ("Command Injection", "HIGH"),
    "os.popen":           ("Command Injection", "HIGH"),
    "__import__":         ("Dynamic Import", "MEDIUM"),
    "pickle.load":        ("Unsafe Deserialization", "HIGH"),
    "pickle.loads":       ("Unsafe Deserialization", "HIGH"),
    "yaml.load":          ("YAML Injection", "MEDIUM"),
    "render_template_string": ("XSS Vulnerability", "HIGH"),
}

# Subset of dotted calls that need prefix matching (e.g. subprocess.*)
AST_PREFIX_PATTERNS = [
    ("subprocess.", "shell=True", "Command Injection", "HIGH"),
]

# ── Regex-only patterns (things AST can't easily detect) ─────────────────────
REGEX_ONLY_PATTERNS = [
    (r'cursor\.execute\s*\(\s*f["\']', "SQL Injection", "HIGH"),
    (r'cursor\.execute\s*\(\s*["\'].*%.*["\']', "SQL Injection", "HIGH"),
    (r'cursor\.execute\s*\(\s*["\'].*\{.*\}.*["\']', "SQL Injection", "HIGH"),
    (r'password\s*=\s*["\'][^"\']+["\']', "Hardcoded Credentials", "HIGH"),
    (r'api_key\s*=\s*["\'][^"\']+["\']', "Hardcoded API Key", "HIGH"),
    (r'secret\s*=\s*["\'][^"\']+["\']', "Hardcoded Secret", "HIGH"),
    (r'http://(?!localhost)', "Insecure HTTP Connection", "MEDIUM"),
    (r'assert\s+False', "Assertion Bypass", "LOW"),
]

# ── Full regex fallback (used when tree-sitter doesn't support the language) ─
FULL_REGEX_PATTERNS = [
    (r'eval\s*\(', "Code Injection (eval)", "HIGH"),
    (r'exec\s*\(', "Code Injection (exec)", "HIGH"),
    (r'os\.system\s*\(', "Command Injection", "HIGH"),
    (r'subprocess\..*shell\s*=\s*True', "Command Injection", "HIGH"),
    (r'__import__\s*\(', "Dynamic Import", "MEDIUM"),
    (r'pickle\.loads?\s*\(', "Unsafe Deserialization", "HIGH"),
    (r'yaml\.load\s*\([^)]*Loader\s*=\s*yaml\.FullLoader', "YAML Injection", "MEDIUM"),
    (r'render_template_string\s*\([^)]*\+', "XSS Vulnerability", "HIGH"),
] + REGEX_ONLY_PATTERNS


def _is_tree_sitter_supported(file_path: str) -> bool:
    """Check if tree-sitter has a grammar for this file type and is available."""
    if not parser_available:
        return False
    ext = os.path.splitext(file_path)[1]
    return ext in {".py", ".js", ".jsx", ".java"}


def _scan_with_ast(file_path: str) -> List[RepoVulnerability]:
    """AST-based scanning: uses tree-sitter to find dangerous function calls."""
    vulnerabilities = []
    call_sites = extract_call_sites(file_path)

    for call in call_sites:
        # Direct name match
        if call.function_name in AST_DANGEROUS_CALLS:
            vuln_type, severity = AST_DANGEROUS_CALLS[call.function_name]
            vulnerabilities.append(RepoVulnerability(
                file_path=file_path,
                line_number=call.line_number,
                code_snippet=call.line_text,
                vulnerability_type=vuln_type,
                severity=severity,
            ))
            continue

        # Prefix match for subprocess.* with shell=True
        for prefix, required_text, vuln_type, severity in AST_PREFIX_PATTERNS:
            if call.function_name.startswith(prefix) and required_text in call.full_call:
                vulnerabilities.append(RepoVulnerability(
                    file_path=file_path,
                    line_number=call.line_number,
                    code_snippet=call.line_text,
                    vulnerability_type=vuln_type,
                    severity=severity,
                ))
                break

    return vulnerabilities


def _scan_with_regex(file_path: str, patterns: list) -> List[RepoVulnerability]:
    """Regex-based scanning: line-by-line pattern matching."""
    vulnerabilities = []
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
    except Exception:
        return vulnerabilities

    for line_num, line in enumerate(lines, 1):
        if _is_comment_line(line, file_path):
            continue
        for pattern, vuln_type, severity in patterns:
            if re.search(pattern, line, re.IGNORECASE):
                vulnerabilities.append(RepoVulnerability(
                    file_path=file_path,
                    line_number=line_num,
                    code_snippet=line.strip(),
                    vulnerability_type=vuln_type,
                    severity=severity,
                ))

    return vulnerabilities


def _is_comment_line(line: str, file_path: str) -> bool:
    ext = os.path.splitext(file_path)[1].lower()
    stripped = line.strip()
    if not stripped:
        return False
    if ext == ".py":
        return stripped.startswith("#")
    if ext in {".js", ".jsx", ".java"}:
        return stripped.startswith("//") or stripped.startswith("/*")
    return False


def scan_file(file_path: str) -> List[RepoVulnerability]:
    """Scan a single file for security vulnerabilities.

    Uses tree-sitter AST for supported languages (Python, JS, Java) to
    accurately detect dangerous function calls without false positives from
    comments or strings. Falls back to full regex for unsupported languages.

    Regex-only patterns (SQL injection, hardcoded creds, HTTP) always run
    since they detect things AST analysis can't.
    """
    if _is_tree_sitter_supported(file_path):
        # AST-based detection for function calls
        vulns = _scan_with_ast(file_path)
        # Regex-only patterns for things AST can't detect
        vulns.extend(_scan_with_regex(file_path, REGEX_ONLY_PATTERNS))
    else:
        # Full regex fallback for unsupported languages
        vulns = _scan_with_regex(file_path, FULL_REGEX_PATTERNS)

    # Deduplicate by (file_path, line_number, vulnerability_type)
    seen = set()
    unique_vulns = []
    for v in vulns:
        key = (v.file_path, v.line_number, v.vulnerability_type)
        if key not in seen:
            seen.add(key)
            unique_vulns.append(v)

    return unique_vulns


def scan_repo(files: List[str]) -> List[RepoVulnerability]:
    """Scan all files in a repository for vulnerabilities."""
    all_vulns = []
    for file_path in files:
        all_vulns.extend(scan_file(file_path))
    return all_vulns
