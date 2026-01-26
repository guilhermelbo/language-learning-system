param(
    [Parameter()]
    [switch]$Json
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
    Write-Error "Feature directory not found: $PWD/$specsDir`nRun /speckit.specify first to create the feature structure."
    exit 1
}

# Check for spec file
$specFile = "$specsDir/spec.md"
if (-not (Test-Path $specFile)) {
    Write-Error "spec.md not found. Run /speckit.specify first."
    exit 1
}

# Create plan file if it doesn't exist
$planFile = "$specsDir/plan.md"
if (-not (Test-Path $planFile)) {
    $templatePath = ".specify/templates/plan-template.md"
    if (Test-Path $templatePath) {
        Copy-Item $templatePath $planFile
    } else {
        # Create minimal plan file
        $initialContent = @"
# Implementation Plan

*Feature*: [See spec.md](spec.md)
*Branch*: $currentBranch
*Created*: $(Get-Date -Format "yyyy-MM-dd")

---

## Technical Context

[To be filled during planning]

## Constitution Check

[To be validated against project principles]

## Architecture

[Design decisions and patterns]

## Implementation Phases

[Phased implementation approach]
"@
        Set-Content -Path $planFile -Value $initialContent
    }
}

# Create contracts directory
$contractsDir = "$specsDir/contracts"
if (-not (Test-Path $contractsDir)) {
    New-Item -ItemType Directory -Path $contractsDir -Force | Out-Null
}

# Build result
$result = @{
    FEATURE_SPEC = $specFile
    IMPL_PLAN = $planFile
    SPECS_DIR = $specsDir
    BRANCH = $currentBranch
    CONTRACTS_DIR = $contractsDir
}

if ($Json) {
    $result | ConvertTo-Json
} else {
    Write-Host "Feature spec: $specFile"
    Write-Host "Implementation plan: $planFile"
    Write-Host "Specs directory: $specsDir"
    Write-Host "Branch: $currentBranch"
}
