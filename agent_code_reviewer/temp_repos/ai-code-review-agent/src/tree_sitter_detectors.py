from typing import List, Dict, Any

def ts_detect_xss(path: str, source: str, tree) -> List[Dict[str, Any]]:
    """Tree-sitter based XSS detection using node traversal (query-like).
    This function expects a tree-sitter `Tree` from `parser.parse_with_tree_sitter`.
    It looks for property identifiers named `innerHTML` and call expressions containing `document.write`.
    """
    issues: List[Dict[str, Any]] = []
    try:
        root = tree.root_node
    except Exception:
        return issues

    def walk(node):
        try:
            # detect innerHTML property usages
            if node.type in ('property_identifier', 'property_name', 'identifier'):
                text = source[node.start_byte:node.end_byte]
                if isinstance(text, bytes):
                    text = text.decode('utf8', errors='ignore')
                if text == 'innerHTML':
                    lineno = source[:node.start_byte].count('\n') + 1
                    snippet = ''
                    try:
                        snippet = source.splitlines()[lineno - 1].strip()
                    except Exception:
                        snippet = ''
                    issues.append({'file': path, 'line': lineno, 'type': 'XSS', 'message': 'innerHTML usage detected (tree-sitter)', 'confidence': 0.8, 'snippet': snippet, 'suggestion': 'Sanitize or use textContent.'})

            # detect document.write call expressions
            if node.type == 'call_expression':
                text = source[node.start_byte:node.end_byte]
                if isinstance(text, bytes):
                    text = text.decode('utf8', errors='ignore')
                if 'document.write' in text or 'document.writeln' in text:
                    lineno = source[:node.start_byte].count('\n') + 1
                    issues.append({'file': path, 'line': lineno, 'type': 'XSS', 'message': 'document.write detected (tree-sitter)', 'confidence': 0.8, 'snippet': text.strip(), 'suggestion': 'Avoid document.write; sanitize input.'})
        except Exception:
            pass
        for c in node.children:
            walk(c)

    walk(root)
    return issues
