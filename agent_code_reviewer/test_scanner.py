import pytest
import os
import tempfile
from core.scanner import scan_file, scan_repo


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def vuln_py_file(tmp_path):
    """Create a Python file with known vulnerabilities."""
    code = '''import os
import pickle

def dangerous_function(user_input, username):
    # Code injection
    eval(user_input)
    exec(user_input)

    # Command injection
    os.system("rm -rf " + user_input)

    # Unsafe deserialization
    data = pickle.loads(user_input)

    # Hardcoded credentials
    password = "super_secret_password"
    api_key = "AKIAIOSFODNN7EXAMPLE"
    secret = "my_secret_key_12345"

    # SQL injection
    cursor.execute(f"SELECT * FROM users WHERE id = '{username}'")

    # Insecure HTTP
    requests.get("http://example.com/api")
'''
    f = tmp_path / "vulnerable.py"
    f.write_text(code)
    return str(f)


@pytest.fixture
def clean_py_file(tmp_path):
    """Create a Python file with NO vulnerabilities."""
    code = '''import os
import json

def safe_function(data):
    result = json.loads(data)
    name = result.get("name", "unknown")
    print(f"Hello, {name}")
    return name
'''
    f = tmp_path / "clean.py"
    f.write_text(code)
    return str(f)


@pytest.fixture
def vuln_js_file(tmp_path):
    """Create a JavaScript file with known vulnerabilities."""
    code = '''const password = "admin123";
const api_key = "sk-1234567890abcdef";

function dangerous(input) {
    eval(input);
    fetch("http://insecure-api.com/data");
}
'''
    f = tmp_path / "vulnerable.js"
    f.write_text(code)
    return str(f)


@pytest.fixture
def comment_only_py(tmp_path):
    """Python file where 'eval' only appears in a comment."""
    code = '''# Do NOT use eval() here, it's dangerous
def safe():
    return 42
'''
    f = tmp_path / "comment_eval.py"
    f.write_text(code)
    return str(f)


# ── Test: Python vulnerability detection ─────────────────────────────────────

class TestPythonScanning:
    def test_detects_eval(self, vuln_py_file):
        vulns = scan_file(vuln_py_file)
        assert any(v.vulnerability_type == "Code Injection (eval)" for v in vulns)

    def test_detects_exec(self, vuln_py_file):
        vulns = scan_file(vuln_py_file)
        assert any(v.vulnerability_type == "Code Injection (exec)" for v in vulns)

    def test_detects_command_injection(self, vuln_py_file):
        vulns = scan_file(vuln_py_file)
        assert any(v.vulnerability_type == "Command Injection" for v in vulns)

    def test_detects_unsafe_deserialization(self, vuln_py_file):
        vulns = scan_file(vuln_py_file)
        assert any(v.vulnerability_type == "Unsafe Deserialization" for v in vulns)

    def test_detects_hardcoded_credentials(self, vuln_py_file):
        vulns = scan_file(vuln_py_file)
        assert any(v.vulnerability_type == "Hardcoded Credentials" for v in vulns)

    def test_detects_hardcoded_api_key(self, vuln_py_file):
        vulns = scan_file(vuln_py_file)
        assert any(v.vulnerability_type == "Hardcoded API Key" for v in vulns)

    def test_detects_sql_injection(self, vuln_py_file):
        vulns = scan_file(vuln_py_file)
        assert any(v.vulnerability_type == "SQL Injection" for v in vulns)

    def test_detects_insecure_http(self, vuln_py_file):
        vulns = scan_file(vuln_py_file)
        assert any(v.vulnerability_type == "Insecure HTTP Connection" for v in vulns)

    def test_clean_file_has_no_vulns(self, clean_py_file):
        vulns = scan_file(clean_py_file)
        assert len(vulns) == 0, f"Expected 0 vulnerabilities, got {len(vulns)}: {[v.vulnerability_type for v in vulns]}"

    def test_severity_is_set(self, vuln_py_file):
        vulns = scan_file(vuln_py_file)
        for v in vulns:
            assert v.severity in ("HIGH", "MEDIUM", "LOW"), f"Bad severity: {v.severity}"

    def test_line_numbers_are_positive(self, vuln_py_file):
        vulns = scan_file(vuln_py_file)
        for v in vulns:
            assert v.line_number > 0

    def test_no_duplicate_vulns(self, vuln_py_file):
        vulns = scan_file(vuln_py_file)
        keys = [(v.file_path, v.line_number, v.vulnerability_type) for v in vulns]
        assert len(keys) == len(set(keys)), "Duplicate vulnerabilities detected"


# ── Test: JavaScript scanning ────────────────────────────────────────────────

class TestJavaScriptScanning:
    def test_detects_eval_in_js(self, vuln_js_file):
        vulns = scan_file(vuln_js_file)
        assert any(v.vulnerability_type == "Code Injection (eval)" for v in vulns)

    def test_detects_hardcoded_creds_in_js(self, vuln_js_file):
        vulns = scan_file(vuln_js_file)
        assert any(v.vulnerability_type in ("Hardcoded Credentials", "Hardcoded API Key") for v in vulns)

    def test_detects_insecure_http_in_js(self, vuln_js_file):
        vulns = scan_file(vuln_js_file)
        assert any(v.vulnerability_type == "Insecure HTTP Connection" for v in vulns)


# ── Test: AST vs Regex accuracy ──────────────────────────────────────────────

class TestASTAccuracy:
    def test_comment_eval_not_detected(self, comment_only_py):
        """AST should NOT flag eval() that only appears inside a comment."""
        vulns = scan_file(comment_only_py)
        eval_vulns = [v for v in vulns if v.vulnerability_type == "Code Injection (eval)"]
        assert len(eval_vulns) == 0, "AST scanner should not flag eval in comments"


# ── Test: scan_repo ──────────────────────────────────────────────────────────

class TestScanRepo:
    def test_scan_repo_combines_results(self, vuln_py_file, clean_py_file):
        vulns = scan_repo([vuln_py_file, clean_py_file])
        assert len(vulns) > 0
        assert all(v.file_path == vuln_py_file for v in vulns)

    def test_scan_repo_empty_list(self):
        vulns = scan_repo([])
        assert vulns == []

    def test_scan_nonexistent_file(self, tmp_path):
        vulns = scan_file(str(tmp_path / "does_not_exist.py"))
        assert vulns == []


# ── Test: RepoVulnerability model ────────────────────────────────────────────

class TestRepoVulnerability:
    def test_to_dict(self, vuln_py_file):
        vulns = scan_file(vuln_py_file)
        assert len(vulns) > 0
        d = vulns[0].to_dict()
        assert "file_path" in d
        assert "line_number" in d
        assert "code_snippet" in d
        assert "vulnerability_type" in d
        assert "severity" in d
