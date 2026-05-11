from src.parser import tree_sitter_available, parse_with_tree_sitter
import sys

def main():
    ok = tree_sitter_available()
    print('tree_sitter bundle available:', ok)
    if not ok:
        print('No bundle found. See TREE_SITTER_SETUP.md for instructions to build one.')
        return 1
    code = "document.getElementById('out').innerHTML = userContent;"
    tree = parse_with_tree_sitter('javascript', code)
    print('parsed tree:', bool(tree))
    if tree:
        # simple traversal demonstration
        root = tree.root_node
        print('root type:', root.type)
    return 0

if __name__ == '__main__':
    sys.exit(main())
