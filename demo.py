from pathlib import Path
from core.scanner import scan_file
from collections import defaultdict

# Create a new sample vulnerable file
sample_path = Path("new_vulnerable.py")
code = '''import os
import subprocess
import yaml
from flask import Flask, request

app = Flask(__name__)

@app.route('/login')
def login():
    username = request.args.get('user')
    password = request.args.get('pass')

    # XSS Vulnerability
    return f"<h1>Welcome {username}!</h1>"

@app.route('/run')
def run_command():
    cmd = request.args.get('cmd')

    # Command Injection
    result = subprocess.run(cmd, shell=True, capture_output=True)
    return result.stdout.decode()

@app.route('/load_config')
def load_config():
    config_data = request.data.decode()

    # YAML Injection
    config = yaml.load(config_data)
    return str(config)

# Hardcoded API Key
API_KEY = "sk-1234567890abcdef"

# Unsafe Deserialization
import pickle
def load_data(data):
    return pickle.loads(data)

# Dynamic Import
def import_module(name):
    return __import__(name)
'''

sample_path.write_text(code, encoding="utf-8")
print(f"🔍 Scanning: {sample_path.resolve()}")

vulns = scan_file(str(sample_path))

if not vulns:
    print("✅ No vulnerabilities found!")
else:
    print(f"\n🚨 Found {len(vulns)} vulnerabilities:\n")

    # Group by severity
    by_severity = defaultdict(list)
    for v in vulns:
        by_severity[v.severity].append(v)

    # Print by severity (HIGH first)
    for severity in ["HIGH", "MEDIUM", "LOW"]:
        if severity in by_severity:
            print(f"🔴 {severity} Severity:")
            for v in by_severity[severity]:
                print(f"  📁 {v.file_path}:{v.line_number}")
                print(f"  💻 {v.code_snippet}")
                print(f"  ⚠️  {v.vulnerability_type}")
                print()

