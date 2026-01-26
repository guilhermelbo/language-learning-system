param(
    [Parameter()]
    [string]$AgentType = "claude"
)

$ErrorActionPreference = "Stop"

# Get current branch
$currentBranch = git rev-parse --abbrev-ref HEAD 2>$null
if (-not $currentBranch) {
    Write-Error "Not in a git repository"
    exit 1
}

# Determine feature directory
$specsDir = "specs/$currentBranch"

if (-not (Test-Path $specsDir)) {
    Write-Error "Feature directory not found: $PWD/$specsDir"
    exit 1
}

# Read plan file to extract technology context
$planFile = "$specsDir/plan.md"
if (-not (Test-Path $planFile)) {
    Write-Host "No plan.md found, skipping agent context update"
    exit 0
}

$planContent = Get-Content $planFile -Raw

# Determine agent context file
$agentContextFile = switch ($AgentType) {
    "claude" { ".claude/settings.local.json" }
    "cursor" { ".cursor/settings.json" }
    default { ".ai/context.json" }
}

Write-Host "Agent type: $AgentType"
Write-Host "Context file: $agentContextFile"
Write-Host "Updated from: $planFile"

# For now, just report what would be updated
# Actual implementation would parse plan.md and update agent-specific context

Write-Host "Agent context update complete (no-op for now)"
