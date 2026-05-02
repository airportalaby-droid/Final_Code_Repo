import os
from typing import List, Optional, Tuple
from dataclasses import dataclass

try:
    import tree_sitter_python as tspython
    import tree_sitter_javascript as tsjavascript
    import tree_sitter_java as tsjava
    from tree_sitter import Language, Parser
    parser_available = True
except ImportError:
    tspython = tsjavascript = tsjava = None
    Language = None  # type: ignore[assignment]
    Parser = None  # type: ignore[assignment]
    parser_available = False


LANGUAGE_MAP = {
    ".py": tspython.language if tspython else None,
    ".js": tsjavascript.language if tsjavascript else None,
    ".jsx": tsjavascript.language if tsjavascript else None,
    ".java": tsjava.language if tsjava else None,
}
LANGUAGE_MAP = {k: v for k, v in LANGUAGE_MAP.items() if v is not None}


@dataclass
class ASTCallSite:
    """Represents a function/method call found in the AST."""
    function_name: str
    full_call: str
    line_number: int
    line_text: str


def get_parser(file_path: str) -> Optional[Parser]:
    if not parser_available:
        return None
    ext = os.path.splitext(file_path)[1]
    lang_func = LANGUAGE_MAP.get(ext)
    if lang_func:
        return Parser(Language(lang_func()))
    return None


def parse_code(file_path: str) -> Tuple[Optional[object], str]:
    parser = get_parser(file_path)
    if not parser:
        return None, ""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            code = f.read()
        tree = parser.parse(bytes(code, "utf8"))
        return tree, code
    except Exception:
        return None, ""


def _walk_tree(node):
    """Recursively yield all nodes in the tree."""
    yield node
    for child in node.children:
        yield from _walk_tree(child)


def _extract_call_name(node, source_lines: List[str]) -> Optional[str]:
    """Extract the full function name from a call node.

    Handles:
      - Simple calls: eval(...) -> "eval"
      - Attribute calls: os.system(...) -> "os.system"
      - Chained: subprocess.run(...) -> "subprocess.run"
    """
    if node.type in ("call", "call_expression"):
        func_node = node.child_by_field_name("function")
        if func_node is None and node.children:
            func_node = node.children[0]
        if func_node is None:
            return None

        if func_node.type == "identifier":
            return func_node.text.decode("utf-8")
        elif func_node.type in ("attribute", "member_expression"):
            return func_node.text.decode("utf-8")

    # Java: method_invocation
    if node.type == "method_invocation":
        obj = node.child_by_field_name("object")
        method = node.child_by_field_name("name")
        if obj and method:
            return f"{obj.text.decode('utf-8')}.{method.text.decode('utf-8')}"
        elif method:
            return method.text.decode("utf-8")

    return None


def extract_call_sites(file_path: str) -> List[ASTCallSite]:
    """Parse a file and return all function/method call sites."""
    tree, code = parse_code(file_path)
    if tree is None or not code:
        return []

    source_lines = code.splitlines()
    call_sites = []

    call_node_types = {"call", "call_expression", "method_invocation"}

    for node in _walk_tree(tree.root_node):
        if node.type in call_node_types:
            func_name = _extract_call_name(node, source_lines)
            if func_name:
                line_num = node.start_point[0] + 1  # 1-indexed
                line_text = source_lines[node.start_point[0]] if node.start_point[0] < len(source_lines) else ""
                call_sites.append(ASTCallSite(
                    function_name=func_name,
                    full_call=node.text.decode("utf-8"),
                    line_number=line_num,
                    line_text=line_text.strip(),
                ))

    return call_sites
