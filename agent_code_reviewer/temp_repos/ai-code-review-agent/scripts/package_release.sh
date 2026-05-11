#!/usr/bin/env bash
# Package a review-ready zip containing key files for sharing with reviewers
set -euo pipefail

ROOT=$(cd "$(dirname "$0")/.." && pwd)
OUT="$ROOT/release"
mkdir -p "$OUT"
TS=$(date +%Y%m%d-%H%M%S)
NAME="ast-static-analysis-review-$TS.zip"

echo "Packaging release to $OUT/$NAME"
cd "$ROOT"

zip -r "$OUT/$NAME" \
  src demo_runner.py samples tests requirements.txt README.md RELEASE_NOTES.md TREE_SITTER_SETUP.md .github scripts || true

echo "Created $OUT/$NAME"
