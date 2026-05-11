from src.parser import parse_file
from src.detectors import detect_sql_injection


def run_test(name: str, code: str, expect_vuln: bool):
    parsed = parse_file(name, code)
    findings = detect_sql_injection(name, parsed['source'], parsed.get('tree'))
    has = len(findings) > 0
    print(f"{name}: expected_vuln={expect_vuln} -> found={has}")
    if expect_vuln and not has:
        print("  FAIL: expected vulnerability but none found")
        print("  findings:", findings)
        return 1
    if not expect_vuln and has:
        print("  FAIL: unexpected vulnerability found")
        print("  findings:", findings)
        return 1
    print("  OK")
    return 0


def main():
    tests = []

    # Vulnerable: f-string used in execute without parameters
    tests.append(("vuln_fstring.py", "cursor.execute(f\"SELECT * FROM users WHERE name = '{user}'\")", True))

    # Vulnerable: string concatenation
    tests.append(("vuln_concat.py", "sql = 'SELECT * FROM users WHERE id=' + user\ncursor.execute(sql)", True))

    # Safe: parameterized
    tests.append(("safe_param.py", "cursor.execute('SELECT * FROM users WHERE id=%s', (user,))", False))

    # Safe: static query
    tests.append(("safe_static.py", "cursor.execute('SELECT 1')", False))

    failures = 0
    for name, code, expect in tests:
        failures += run_test(name, code, expect)

    if failures:
        print(f"{failures} tests failed")
        raise SystemExit(2)
    print("All SQLi AST tests passed")


if __name__ == '__main__':
    main()
