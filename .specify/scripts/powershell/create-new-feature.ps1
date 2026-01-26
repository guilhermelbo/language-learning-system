param(
    [Parameter(Position=0)]
    [string]$Description,

    [Parameter()]
    [switch]$Json,

    [Parameter()]
    [int]$Number = 1,

    [Parameter()]
    [string]$ShortName
)

$ErrorActionPreference = "Stop"

# Validate inputs
if (-not $ShortName) {
    Write-Error "ShortName is required"
    exit 1
}

if (-not $Description) {
    Write-Error "Description is required"
    exit 1
}

# Create branch name
$BranchName = "$Number-$ShortName"

# Create specs directory
$SpecsDir = "specs/$BranchName"
$SpecFile = "$SpecsDir/spec.md"
$ChecklistsDir = "$SpecsDir/checklists"

# Create directories
New-Item -ItemType Directory -Path $SpecsDir -Force | Out-Null
New-Item -ItemType Directory -Path $ChecklistsDir -Force | Out-Null

# Create initial spec file
$InitialContent = @"
# Feature Specification: $Description

*Status: Draft*
*Created: $(Get-Date -Format "yyyy-MM-dd")*
*Branch: $BranchName*

---

[Specification content will be written here]
"@

Set-Content -Path $SpecFile -Value $InitialContent

# Create and checkout branch
git checkout -b $BranchName 2>$null
if ($LASTEXITCODE -ne 0) {
    # Branch might already exist, try to checkout
    git checkout $BranchName 2>$null
}

# Output JSON if requested
if ($Json) {
    $result = @{
        BRANCH_NAME = $BranchName
        SPEC_FILE = $SpecFile
        FEATURE_DIR = $SpecsDir
        CHECKLISTS_DIR = $ChecklistsDir
        DESCRIPTION = $Description
    }
    $result | ConvertTo-Json
} else {
    Write-Host "Created feature branch: $BranchName"
    Write-Host "Spec file: $SpecFile"
}
