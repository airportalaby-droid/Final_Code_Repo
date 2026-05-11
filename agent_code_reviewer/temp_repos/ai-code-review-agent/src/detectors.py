import re
import ast
from typing import List, Dict, Any

try:
    from tree_sitter import Node
    TREE_SITTER_NODE_AVAILABLE = True
except Exception:
    TREE_SITTER_NODE_AVAILABLE = False

from src.parser import tree_sitter_available
try:
    from .tree_sitter_detectors import ts_detect_xss
except Exception:
    ts_detect_xss = None


def _line_from_index(source: str, index: int) -> int:
    return source[:index].count('\n') + 1


def _is_sql_call(node: ast.Call) -> bool:
    func = node.func
    if isinstance(func, ast.Attribute):
        name = func.attr
    elif isinstance(func, ast.Name):
        name = func.id
    else:
        return False
    return name.lower() in ('execute', 'executemany', 'query', 'run')


def _call_has_params(node: ast.Call) -> bool:
    if len(node.args) >= 2:
        return True
    for kw in node.keywords:
        if kw.arg and kw.arg.lower() in ('params', 'parameters', 'args'):
            return True
    return False


def detect_sql_injection(path: str, source: str, tree=None) -> List[Dict[str, Any]]:
    issues: List[Dict[str, Any]] = []

    # AST-based for Python
    if isinstance(tree, ast.AST):
        # gather simple assignments to resolve names used as query variables
        assigns = {}
        for n in ast.walk(tree):
            if isinstance(n, ast.Assign):
                for t in n.targets:
                    if isinstance(t, ast.Name):
                        assigns[t.id] = n.value

        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and _is_sql_call(node):
                if not node.args:
                    continue
                sql_expr = node.args[0]
                # resolve name to assigned expression if available
                if isinstance(sql_expr, ast.Name):
                    resolved = assigns.get(sql_expr.id)
                    if resolved is not None:
                        sql_expr = resolved
                unsafe = False
                if isinstance(sql_expr, ast.JoinedStr):
                    unsafe = True
                elif isinstance(sql_expr, ast.BinOp) and isinstance(sql_expr.op, (ast.Add, ast.Mod)):
                    unsafe = True
                elif isinstance(sql_expr, ast.Call) and isinstance(sql_expr.func, ast.Attribute) and sql_expr.func.attr == 'format':
                    unsafe = True

                if unsafe and not _call_has_params(node):
                    lineno = getattr(node, 'lineno', 1)
                    try:
                        snippet = source.splitlines()[lineno - 1].strip()
                    except Exception:
                        snippet = ''
                    issues.append({
                        'file': path,
                        'line': lineno,
                        'type': 'SQL Injection',
                        'message': 'Possible SQL built with string ops or f-strings in DB call',
                        'confidence': 0.9,
                        'snippet': snippet,
                        'suggestion': 'Use parameterized queries / prepared statements.'
                    })
        return issues

    # Regex fallback for other languages
    patterns = [r"cursor\.execute\((.+)\)", r"execute\((.+)\)", r"db\.query\((.+)\)"]
    for pat in patterns:
        for m in re.finditer(pat, source):
            group = m.group(1)
            if re.search(r"\+|%|format\(|f\"|f'", group):
                lineno = _line_from_index(source, m.start())
                issues.append({
                    'file': path,
                    'line': lineno,
                    'type': 'SQL Injection',
                    'message': 'Possible SQL constructed via string formatting/concatenation',
                    'confidence': 0.7,
                    'snippet': source.splitlines()[max(0, lineno-1)].strip(),
                    'suggestion': 'Use parameterized queries.'
                })
    return issues


def _xss_tree_sitter_scan(path: str, source: str, tree) -> List[Dict[str, Any]]:
    issues: List[Dict[str, Any]] = []
    try:
        root = tree.root_node
    except Exception:
        return issues

    def walk(n):
        try:
            if n.type in ('property_identifier', 'property_name', 'identifier'):
                raw = source[n.start_byte:n.end_byte]
                if isinstance(raw, bytes):
                    raw = raw.decode('utf8', errors='ignore')
                if raw == 'innerHTML':
                    lineno = _line_from_index(source, n.start_byte)
                    issues.append({'file': path, 'line': lineno, 'type': 'XSS', 'message': 'innerHTML usage detected', 'confidence': 0.75, 'snippet': source.splitlines()[lineno-1].strip(), 'suggestion': 'Sanitize or use textContent.'})
            if n.type == 'call_expression':
                raw = source[n.start_byte:n.end_byte]
                if isinstance(raw, bytes):
                    raw = raw.decode('utf8', errors='ignore')
                if 'document.write' in raw or 'document.writeln' in raw:
                    lineno = _line_from_index(source, n.start_byte)
                    issues.append({'file': path, 'line': lineno, 'type': 'XSS', 'message': 'document.write detected', 'confidence': 0.75, 'snippet': raw.strip(), 'suggestion': 'Avoid document.write; sanitize input.'})
        except Exception:
            pass
        for c in n.children:
            walk(c)

    walk(root)
    return issues


def detect_xss(path: str, source: str, tree=None) -> List[Dict[str, Any]]:
    issues: List[Dict[str, Any]] = []
    # Prefer tree-sitter query-based (or traversal) detection when available
    if tree is not None and tree_sitter_available() and ts_detect_xss is not None:
        try:
            issues.extend(ts_detect_xss(path, source, tree))
        except Exception:
            # fallback to older traversal when anything fails
            try:
                issues.extend(_xss_tree_sitter_scan(path, source, tree))
            except Exception:
                pass
    elif tree is not None and TREE_SITTER_NODE_AVAILABLE:
        try:
            issues.extend(_xss_tree_sitter_scan(path, source, tree))
        except Exception:
            pass

    # Regex fallback
    for pat in [r"innerHTML\s*=" , r"document\.write\(|document\.writeln\(", r"\.innerHTML\s*\+"]:
        for m in re.finditer(pat, source):
            lineno = _line_from_index(source, m.start())
            issues.append({'file': path, 'line': lineno, 'type': 'XSS', 'message': 'Suspicious DOM sink detected', 'confidence': 0.6, 'snippet': source.splitlines()[max(0, lineno-1)].strip(), 'suggestion': 'Sanitize user input before DOM insertion.'})
    return issues


def detect_hardcoded_secrets(path: str, source: str, tree=None) -> List[Dict[str, Any]]:
    issues: List[Dict[str, Any]] = []
    patterns = {
        'AWS Access Key': r"AKIA[0-9A-Z]{16}",
        'Private Key Block': r"-----BEGIN PRIVATE KEY-----",
        'Generic API Key': r"(?i)api[_-]?key\s*[:=]\s*['\"]?[A-Za-z0-9\-_.]{16,}['\"]?",
        'Password Assignment': r"(?i)password\s*[:=]\s*['\"].{6,}['\"]",
    }
    seen = set()
    for name, pat in patterns.items():
        for m in re.finditer(pat, source):
            lineno = _line_from_index(source, m.start())
            key = (path, lineno, name)
            if key in seen:
                continue
            seen.add(key)
            issues.append({'file': path, 'line': lineno, 'type': 'Hardcoded Secret', 'message': f'{name} found', 'confidence': 0.85 if name == 'AWS Access Key' else 0.7, 'snippet': source.splitlines()[max(0, lineno-1)].strip(), 'suggestion': 'Move secret to env or secret store.'})
    return issues


def run_detectors(path: str, parsed: Dict[str, Any]) -> List[Dict[str, Any]]:
    source = parsed.get('source', '')
    tree = parsed.get('tree')
    results: List[Dict[str, Any]] = []
    results.extend(detect_sql_injection(path, source, tree))
    results.extend(detect_xss(path, source, tree))
    results.extend(detect_hardcoded_secrets(path, source, tree))

    # dedupe
    seen = set()
    out: List[Dict[str, Any]] = []
    for r in results:
        k = (r.get('file'), r.get('line'), r.get('type'), r.get('message'))
        if k in seen:
            continue
        seen.add(k)
        out.append(r)
    return out
