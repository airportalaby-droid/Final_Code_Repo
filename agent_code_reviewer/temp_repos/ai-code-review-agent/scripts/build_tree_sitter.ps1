<# PowerShell script to build tree-sitter language bundle on Windows (prefer WSL) #>
Param()

Write-Output "This script assumes you run it in WSL or have a working GCC/mingw toolchain."
Write-Output "Recommended: run from WSL (open Ubuntu on Windows) and run the bash script: ./scripts/build_tree_sitter.sh"

if ($IsWindows) {
    Write-Output "On Windows, use WSL and run the bash helper. Exiting."
    exit 0
}
