import tree_sitter_python as tspython
from tree_sitter import Language, Parser

# New API (tree-sitter >= 0.21.0)
PY_LANGUAGE = Language(tspython.language())
parser = Parser(PY_LANGUAGE)

# Query syntax updated for newer versions
query_string = """
    (call
        function: (identifier) @func_name
        (#match? @func_name "^(eval|exec)$")) @dangerous_call
"""

query = PY_LANGUAGE.query(query_string)

source = b"eval('ls')"
tree = parser.parse(source)

matches = query.matches(tree.root_node)
print("Matches:", matches)
