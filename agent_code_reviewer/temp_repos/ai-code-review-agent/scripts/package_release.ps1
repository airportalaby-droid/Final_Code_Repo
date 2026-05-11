param()
Write-Output "Packaging review bundle (PowerShell)"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$out = Join-Path $root '..\release' | Resolve-Path -LiteralPath
if (-not (Test-Path $out)) { New-Item -ItemType Directory -Path $out | Out-Null }
$ts = Get-Date -Format yyyyMMdd-HHmmss
$name = "ast-static-analysis-review-$ts.zip"
$zipPath = Join-Path $out $name

Compress-Archive -Path src, demo_runner.py, samples, tests, requirements.txt, README.md, RELEASE_NOTES.md, TREE_SITTER_SETUP.md, .github, scripts -DestinationPath $zipPath -Force
Write-Output "Created $zipPath"
