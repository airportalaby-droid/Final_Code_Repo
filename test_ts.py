import pytest

pytest.importorskip("tree_sitter_python")
pytest.importorskip("tree_sitter")

import tree_sitter_python as tspython
from tree_sitter import Language, Parser


def test_tree_sitter_python_query():
    """Verify Tree-sitter can parse a simple Python eval call."""
    PY_LANGUAGE = Language(tspython.language())
    parser = Parser(PY_LANGUAGE)

    query_string = """
        (call
            function: (identifier) @func_name
            (#match? @func_name "^(eval|exec)$")) @dangerous_call
    """

    query = PY_LANGUAGE.query(query_string)
    source = b"eval('ls')"
    tree = parser.parse(source)

    matches = query.matches(tree.root_node)
    assert len(matches) > 0
