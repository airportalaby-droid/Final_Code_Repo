## Building tree-sitter languages bundle (quick guide)

This project supports optional tree-sitter parsing for JS/TS/HTML when a combined language bundle is available.

Quick steps (recommended: use WSL on Windows):

1. Install Python dev tools and tree-sitter package

```bash
python3 -m pip install --upgrade pip setuptools wheel
python3 -m pip install tree_sitter
```

2. Run the provided helper (in WSL or Linux/macOS):

```bash
./scripts/build_tree_sitter.sh
```

3. After a successful build the bundle will be at `build/my-languages.so`. Set this env var before running the app:

Windows (PowerShell):

```powershell
$env:TREE_SITTER_LANG_SO = "D:\path\to\Agent_AI\build\my-languages.so"
```

Linux/WSL/macOS (bash):

```bash
export TREE_SITTER_LANG_SO="$(pwd)/build/my-languages.so"
```

4. Verify from Python:

```bash
python -c "from src.parser import tree_sitter_available; print(tree_sitter_available())"
```

Notes:
- Building requires a C compiler. On Windows prefer WSL (Ubuntu) to avoid toolchain issues.
- You can include additional grammars by adding their repo paths to `scripts/build_tree_sitter.sh`.
