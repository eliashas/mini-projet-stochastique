param([string]$Python = 'python', [string]$KitDir = '')
$ErrorActionPreference = 'Stop'
$projectDir = Split-Path -Parent $PSScriptRoot
Push-Location -LiteralPath $projectDir
try {
    $extraArgs = @()
    if ($KitDir) { $extraArgs = @('--kit-dir', $KitDir) }
    & $Python scripts/run_pipeline.py all --config configs/experiments.yaml @extraArgs
    if ($LASTEXITCODE -ne 0) { throw 'Pipeline failed; see artifacts/execution_journal.jsonl' }
} finally { Pop-Location }
