import json
import sys
import os

# Ensure workspace root is on sys.path so tests can import `src`
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.parser import parse_file
from src.detectors import run_detectors


def _load_sample(path):
    with open(path, 'r', encoding='utf-8') as fh:
        return fh.read()


def test_vulnerable_py():
    src = _load_sample('samples/vulnerable.py')
    parsed = parse_file('samples/vulnerable.py', src)
    issues = run_detectors('samples/vulnerable.py', parsed)
    assert any(i['type'] == 'Hardcoded Secret' for i in issues)
    assert any(i['type'] == 'SQL Injection' for i in issues)


def test_vulnerable_js():
    src = _load_sample('samples/vulnerable.js')
    parsed = parse_file('samples/vulnerable.js', src)
    issues = run_detectors('samples/vulnerable.js', parsed)
    assert any(i['type'] == 'XSS' for i in issues)
