import ast
import os
from typing import Optional, Dict, Any

try:
    from tree_sitter import Language, Parser
    TREE_SITTER_AVAILABLE = True
except Exception:
    TREE_SITTER_AVAILABLE = False


def detect_language_by_extension(path: str) -> str:
    ext = path.lower().rsplit('.', 1)[-1]
    if ext in ('py',):
        return 'python'
    if ext in ('js', 'jsx'):
        return 'javascript'
    if ext in ('ts', 'tsx'):
        return 'typescript'
    if ext in ('html', 'htm'):
        return 'html'
    if ext in ('php',):
        return 'php'
    return 'text'


def parse_python(source: str) -> Optional[ast.AST]:
    try:
        return ast.parse(source)
    except Exception:
        return None


_TS_PARSER = None


def _init_tree_sitter():
    """Attempt to initialize a tree-sitter Parser if a compiled language bundle is available.

    To enable full tree-sitter support, build a combined library and set `TREE_SITTER_LANG_SO`
    env var to its path, or place it at `build/my-languages.so`.
    """
    global _TS_PARSER
    if not TREE_SITTER_AVAILABLE:
        return None
    if _TS_PARSER is not None:
        return _TS_PARSER

    so_path = os.getenv('TREE_SITTER_LANG_SO', os.path.join(os.getcwd(), 'build', 'my-languages.so'))
    if not os.path.exists(so_path):
        return None

    try:
        LANGS = {}
        # Try common languages; Language() will raise if not compiled into the .so
        for name in ('javascript', 'typescript', 'html', 'php'):
            try:
                LANGS[name] = Language(so_path, name)
            except Exception:
                LANGS[name] = None

        parser = Parser()
        _TS_PARSER = (parser, LANGS)
        return _TS_PARSER
    except Exception:
        return None


def parse_with_tree_sitter(lang: str, source: str):
    init = _init_tree_sitter()
    if not init:
        return None
    parser, langs = init
    lang_obj = langs.get(lang)
    if not lang_obj:
        return None
    parser.set_language(lang_obj)
    try:
        return parser.parse(bytes(source, 'utf8'))
    except Exception:
        return None


def tree_sitter_available() -> bool:
    """Return True if a compiled tree-sitter languages bundle is available and usable."""
    return _init_tree_sitter() is not None


def parse_file(path: str, source: str) -> Dict[str, Any]:
    lang = detect_language_by_extension(path)
    result = {"language": lang, "source": source, "tree": None}

    if lang == 'python':
        result['tree'] = parse_python(source)
    else:
        # try tree-sitter when available and compiled languages are provided
        if TREE_SITTER_AVAILABLE:
            ts_tree = parse_with_tree_sitter(lang, source)
            if ts_tree:
                result['tree'] = ts_tree
            else:
                result['tree'] = None
        else:
            result['tree'] = None

    return result
