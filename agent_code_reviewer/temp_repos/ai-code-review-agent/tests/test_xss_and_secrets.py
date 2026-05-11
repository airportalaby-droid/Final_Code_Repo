from src.parser import parse_file
from src.detectors import detect_xss, detect_hardcoded_secrets


def run(name: str, code: str, detector, expect: bool):
    parsed = parse_file(name, code)
    findings = detector(name, parsed['source'], parsed.get('tree'))
    ok = (len(findings) > 0) == expect
    print(f"{name}: expect={expect} -> found={(len(findings) > 0)}")
    if not ok:
        print("  findings:", findings)
        return 1
    print("  OK")
    return 0


def main():
    tests = [
        ("xss_vuln.js", "document.getElementById('out').innerHTML = user;", detect_xss, True),
        ("xss_safe.js", "element.textContent = user;", detect_xss, False),
        ("secret_vuln.py", "API_KEY = \"ABCD1234SECRETKEY\"", detect_hardcoded_secrets, True),
        ("secret_safe.py", "import os\nAPI_KEY = os.getenv('API_KEY')", detect_hardcoded_secrets, False),
    ]

    fails = 0
    for name, code, det, expect in tests:
        fails += run(name, code, det, expect)

    if fails:
        print(f"{fails} tests failed")
        raise SystemExit(2)
    print("All XSS and secrets tests passed")


if __name__ == '__main__':
    main()
