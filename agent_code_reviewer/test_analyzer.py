"""Quick integration test: scan the test_vuln.py fixture file."""
import pytest
from core.scanner import scan_file


def test_scan_test_vuln_file():
    """Scan the local test_vuln.py and verify known vulnerabilities are found."""
    vulns = scan_file("test_vuln.py")
    assert len(vulns) > 0, "Expected vulnerabilities in test_vuln.py"

    vuln_types = {v.vulnerability_type for v in vulns}

    assert "Code Injection (eval)" in vuln_types
    assert "Hardcoded Credentials" in vuln_types
    assert "Hardcoded API Key" in vuln_types
    assert "SQL Injection" in vuln_types


def test_scan_test_vuln_severity():
    """Verify all detected vulns have valid severity values."""
    vulns = scan_file("test_vuln.py")
    for v in vulns:
        assert v.severity in ("HIGH", "MEDIUM", "LOW")
