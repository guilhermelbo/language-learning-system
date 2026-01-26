param(
    [Parameter()]
    [switch]$Json,

    [Parameter()]
    [switch]$RequireTasks,

    [Parameter()]
    [switch]$IncludeTasks
)

$ErrorActionPreference = "Stop"

# Get current branch
$currentBranch = git rev-parse --abbrev-ref HEAD 2>$null
if (-not $currentBranch) {
    Write-Error "Not in a git repository"
    exit 1
}

# Determine feature directory
$featureDir = "specs/$currentBranch"

if (-not (Test-Path $featureDir)) {
    Write-Error "Feature directory not found: $PWD/$featureDir`nRun /speckit.specify first to create the feature structure."
    exit 1
}

# Check for required files
$specFile = "$featureDir/spec.md"
$planFile = "$featureDir/plan.md"
$tasksFile = "$featureDir/tasks.md"

$availableDocs = @()

if (Test-Path $specFile) {
    $availableDocs += "spec"
}

if (Test-Path $planFile) {
    $availableDocs += "plan"
}

if (Test-Path $tasksFile) {
    $availableDocs += "tasks"
}

# Validate requirements
if ($RequireTasks -and -not (Test-Path $tasksFile)) {
    Write-Error "tasks.md not found. Run /speckit.tasks first."
    exit 1
}

# Build result
$result = @{
    FEATURE_DIR = $featureDir
    BRANCH_NAME = $currentBranch
    AVAILABLE_DOCS = $availableDocs
    SPEC_FILE = $specFile
    PLAN_FILE = $planFile
    TASKS_FILE = $tasksFile
}

if ($IncludeTasks -and (Test-Path $tasksFile)) {
    $result.TASKS_CONTENT = Get-Content $tasksFile -Raw
}

if ($Json) {
    $result | ConvertTo-Json
} else {
    Write-Host "Feature directory: $featureDir"
    Write-Host "Available docs: $($availableDocs -join ', ')"
}
