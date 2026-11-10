# Requires Node.js 20.12+, npm/npx, and uv on PATH.
$ErrorActionPreference = 'Stop'
$projectDirectory = Split-Path -Parent $PSScriptRoot
& npx --yes bmad-method@6.12.1 install --directory $projectDirectory `
    --modules bmm --tools codex --user-name LabReserve `
    --communication-language Chinese --document-output-language Chinese `
    --output-folder _bmad-output --set bmm.planning_artifacts=docs `
    --set bmm.implementation_artifacts=. --set bmm.project_knowledge=docs --no-shims --yes
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& uv run (Join-Path $projectDirectory '_bmad/scripts/resolve_config.py') --project-root $projectDirectory
exit $LASTEXITCODE
