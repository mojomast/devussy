#!/usr/bin/env pwsh
# Script to set up devussy-testing repository with clean history

Write-Host "=" * 60
Write-Host "Devussy - New Repository Setup Script"
Write-Host "=" * 60
Write-Host ""

# Step 1: Create the new repository on GitHub
Write-Host "Step 1: Create GitHub Repository"
Write-Host "---------------------------------------"
Write-Host "Please go to: https://github.com/new"
Write-Host "Repository name: devussy-testing"
Write-Host "Description: Devussy - LLM-based development planning tool with terminal streaming UI"
Write-Host "Visibility: Public (or Private)"
Write-Host "DO NOT initialize with README, .gitignore, or license"
Write-Host ""
Write-Host "Press Enter after creating the repository..."
Read-Host

# Step 2: Get the repository URL
Write-Host ""
Write-Host "Step 2: Repository URL"
Write-Host "---------------------------------------"
$repoUrl = Read-Host "Enter the repository URL (e.g., https://github.com/username/devussy-testing.git)"

# Step 3: Create fresh repository with current code
Write-Host ""
Write-Host "Step 3: Creating Fresh Repository"
Write-Host "---------------------------------------"

# Create a temporary directory for the new repo
$tempDir = Join-Path $env:TEMP "devussy-testing-temp"
if (Test-Path $tempDir) {
    Remove-Item -Recurse -Force $tempDir
}
New-Item -ItemType Directory -Path $tempDir | Out-Null

Write-Host "Copying files to temporary directory..."

# Copy all files except .git and problematic directories
$currentDir = Get-Location
$excludeDirs = @('.git', '.pytest_cache', '__pycache__', 'node_modules', '.devussy_state', 'output_0', 'output_1', 'test_output', 'logs')

Get-ChildItem -Path $currentDir -Recurse | Where-Object {
    $item = $_
    $exclude = $false
    foreach ($dir in $excludeDirs) {
        if ($item.FullName -like "*\$dir\*" -or $item.Name -eq $dir) {
            $exclude = $true
            break
        }
    }
    -not $exclude
} | ForEach-Object {
    $relativePath = $_.FullName.Substring($currentDir.Path.Length + 1)
    $targetPath = Join-Path $tempDir $relativePath
    
    if ($_.PSIsContainer) {
        if (-not (Test-Path $targetPath)) {
            New-Item -ItemType Directory -Path $targetPath -Force | Out-Null
        }
    } else {
        $targetDir = Split-Path $targetPath -Parent
        if (-not (Test-Path $targetDir)) {
            New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
        }
        Copy-Item $_.FullName $targetPath -Force
    }
}

Write-Host "Files copied successfully!"

# Initialize new git repository
Write-Host ""
Write-Host "Initializing new git repository..."
Push-Location $tempDir

git init
git add -A
git commit -m "Release 01: Complete Phases 1-5 - Interview Mode & Token Streaming

Major accomplishments:

Phase 1-3: Interview Mode (COMPLETE)
- Repository analysis engine for existing codebases
- LLM-driven interview with context-aware questioning  
- Code sample extraction (architecture, patterns, tests)
- Context-aware devplan generation with repo insights
- Real-world validation with GPT-5 mini via Requesty

Phase 4: Terminal UI Foundation (COMPLETE)
- Textual-based modern TUI with responsive grid layout
- Phase state management with full lifecycle support
- Color-coded status indicators and scrollable content
- Async-first architecture for smooth performance

Phase 5: Token Streaming Integration (COMPLETE)
- Real-time LLM token streaming to terminal UI
- Phase cancellation with clean abort handling
- Concurrent generation of multiple phases
- Regeneration with steering feedback support
- Integration with all LLM providers

Testing & Quality:
- 63 tests passing (56 unit + 7 integration)
- Comprehensive test coverage with zero diagnostics
- Integration tests for full workflows
- Real-world API validation

Documentation:
- Updated README with complete feature list
- Created session summaries (2, 3, 5)
- Updated DEVUSSYPLAN with phase completion status
- Maintained handoff document for circular development

Files added:
- src/interview/ (repository analyzer, code sample extractor)
- src/terminal/ (terminal UI, phase generator, phase state)
- tests/unit/ (15 new test files)
- tests/integration/ (repo-aware pipeline tests)
- scripts/ (demo and integration test scripts)
- docs/ (session summaries, library decision)

Next: Phase 4 rendering enhancements, Phase 6 fullscreen viewer"

# Add remote and push
Write-Host ""
Write-Host "Adding remote and pushing to GitHub..."
git branch -M main
git remote add origin $repoUrl
git push -u origin main

Pop-Location

Write-Host ""
Write-Host "=" * 60
Write-Host "Setup Complete!"
Write-Host "=" * 60
Write-Host ""
Write-Host "Your new repository is ready at:"
Write-Host $repoUrl
Write-Host ""
Write-Host "Temporary directory: $tempDir"
Write-Host "You can delete this after verifying the push succeeded."
Write-Host ""
Write-Host "To continue working with the new repository:"
Write-Host "1. Clone it: git clone $repoUrl"
Write-Host "2. Or update your current remote: git remote set-url origin $repoUrl"
Write-Host ""
