import pytest
from src.parser import parse_with_tree_sitter, tree_sitter_available
from src.tree_sitter_detectors import ts_detect_xss


def test_ts_xss_query_simple():
    if not tree_sitter_available():
        pytest.skip('tree-sitter bundle not available')

    code = "document.getElementById('out').innerHTML = userContent;"
    tree = parse_with_tree_sitter('javascript', code)
    assert tree is not None
    findings = ts_detect_xss('sample.js', code, tree)
    assert any(f['type'] == 'XSS' for f in findings)
