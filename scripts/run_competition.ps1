param([string]$Python = 'python', [string]$KitDir = '')
$ErrorActionPreference = 'Stop'
$projectDir = Split-Path -Parent $PSScriptRoot
Push-Location -LiteralPath $projectDir
try {
    $extraArgs = @()
    if ($KitDir) { $extraArgs = @('--kit-dir', $KitDir) }
    & $Python -m pytest -q
    if ($LASTEXITCODE -ne 0) { throw 'Tests failed' }
    foreach ($phaseCommand in @('audit-data','smoke','validate','select','fit-final','predict','benchmark','report')) {
        & $Python scripts/run_pipeline.py $phaseCommand --config configs/experiments.yaml @extraArgs
        if ($LASTEXITCODE -ne 0) { throw "Phase failed: $phaseCommand" }
    }
} finally { Pop-Location }
