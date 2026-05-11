#!/usr/bin/env bash
# Build a combined tree-sitter language bundle (Linux / WSL / macOS)
set -euo pipefail

echo "== Ensure python and pip are available =="
python3 -m pip install --upgrade pip setuptools wheel

echo "== Install tree_sitter Python package =="
python3 -m pip install tree_sitter

echo "== Clone or ensure grammars are present (adjust versions as needed) =="
mkdir -p vendor
cd vendor
if [ ! -d "tree-sitter-javascript" ]; then
  git clone https://github.com/tree-sitter/tree-sitter-javascript.git
fi
if [ ! -d "tree-sitter-typescript" ]; then
  git clone https://github.com/tree-sitter/tree-sitter-typescript.git
fi
if [ ! -d "tree-sitter-html" ]; then
  git clone https://github.com/tree-sitter/tree-sitter-html.git
fi
cd ..

mkdir -p build
echo "== Building combined library to build/my-languages.so =="
python3 - <<'PY'
from tree_sitter import Language
Language.build_library(
  'build/my-languages.so',
  [
    'vendor/tree-sitter-javascript',
    'vendor/tree-sitter-typescript',
    'vendor/tree-sitter-html',
  ]
)
print('Built build/my-languages.so')
PY

echo "Done. Set TREE_SITTER_LANG_SO=$(pwd)/build/my-languages.so or move the .so to project build/"
