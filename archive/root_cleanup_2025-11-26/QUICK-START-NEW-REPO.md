# Quick Start: Create devussy-testing Repository

## Option 1: Automated Setup (Recommended)

Simply run:
```powershell
.\setup-new-repo.ps1
```

Follow the prompts to create the repository and push the code.

---

## Option 2: Manual Setup (5 Minutes)

### Step 1: Create GitHub Repository (1 min)

1. Go to: https://github.com/new
2. Fill in:
   - **Repository name**: `devussy-testing`
   - **Description**: `Devussy - LLM-based development planning tool with terminal streaming UI`
   - **Visibility**: Public
   - **DO NOT** check any initialization options
3. Click "Create repository"
4. Copy the repository URL (e.g., `https://github.com/yourusername/devussy-testing.git`)

### Step 2: Create Clean Export (2 min)

Open PowerShell in the current devussy directory and run:

```powershell
# Create export directory
$exportDir = "C:\temp\devussy-clean"
New-Item -ItemType Directory -Path $exportDir -Force | Out-Null

# Copy all files except git history and temp files
Get-ChildItem -Path . -Recurse | Where-Object {
    $_.FullName -notmatch '\\\.git\\' -and
    $_.FullName -notmatch '\\\.(pytest_cache|devussy_state)\\' -and
    $_.FullName -notmatch '\\__pycache__\\' -and
    $_.FullName -notmatch '\\(output_|test_output|logs)\\' -and
    $_.Name -ne '.git'
} | ForEach-Object {
    $target = $_.FullName.Replace((Get-Location).Path, $exportDir)
    if ($_.PSIsContainer) {
        New-Item -ItemType Directory -Path $target -Force | Out-Null
    } else {
        $targetDir = Split-Path $target -Parent
        if (-not (Test-Path $targetDir)) {
            New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
        }
        Copy-Item $_.FullName $target -Force
    }
}

Write-Host "✓ Files copied to $exportDir"
```

### Step 3: Initialize and Push (2 min)

```powershell
# Navigate to export directory
cd $exportDir

# Initialize git
git init
git add -A

# Create commit
git commit -m "Release 01: Complete Phases 1-5 - Interview Mode & Token Streaming

Major accomplishments:
- Phase 1-3: Interview Mode (repository analysis, LLM interview, code extraction)
- Phase 4: Terminal UI Foundation (Textual-based TUI, phase state management)
- Phase 5: Token Streaming (real-time LLM streaming, cancellation, concurrent generation)

Testing: 63 tests passing (56 unit + 7 integration)
Documentation: Complete with session summaries and handoff docs"

# Add remote (REPLACE with your actual repository URL)
git remote add origin https://github.com/YOURUSERNAME/devussy-testing.git

# Push to GitHub
git branch -M main
git push -u origin main
```

### Step 4: Verify (30 sec)

1. Go to your repository: `https://github.com/YOURUSERNAME/devussy-testing`
2. Verify files are present
3. Check README displays correctly

---

## What You'll Have

### Repository Structure
```
devussy-testing/
├── src/
│   ├── interview/          # Repository analysis & code extraction
│   ├── terminal/           # Terminal UI & streaming
│   ├── pipeline/           # DevPlan generation
│   ├── clients/            # LLM provider clients
│   └── ...
├── tests/
│   ├── unit/              # 56 unit tests
│   └── integration/       # 7 integration tests
├── scripts/
│   ├── demo_terminal_ui.py
│   ├── test_streaming_integration.py
│   └── test_full_interview_flow.py
├── docs/
│   ├── session-2-summary.md
│   ├── session-3-summary.md
│   ├── session-5-summary.md
│   └── terminal-ui-library-decision.md
├── DEVUSSYPLAN.md
├── devussyhandoff.md
├── RELEASE-01-SUMMARY.md
├── NEW-REPO-INSTRUCTIONS.md
└── README.md
```

### Features Included
- ✅ Interview Mode (Phases 1-3)
- ✅ Terminal UI Foundation (Phase 4)
- ✅ Token Streaming (Phase 5)
- ✅ 63 tests passing
- ✅ Complete documentation

---

## Next Steps After Setup

### 1. Clone Your New Repository
```bash
git clone https://github.com/YOURUSERNAME/devussy-testing.git
cd devussy-testing
```

### 2. Install Dependencies
```bash
pip install -e .
```

### 3. Configure API Keys
Create `.env` file:
```bash
OPENAI_API_KEY=sk-...
# or
REQUESTY_API_KEY=...
```

### 4. Run Tests
```bash
pytest -q
```

### 5. Try the Demos
```bash
# Terminal UI demo
python scripts/demo_terminal_ui.py

# Streaming integration test
python scripts/test_streaming_integration.py
```

---

## Troubleshooting

**Q: Copy command fails?**
A: Run PowerShell as Administrator or adjust the export path

**Q: Push fails with authentication error?**
A: Configure GitHub credentials:
```bash
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

**Q: Files missing after copy?**
A: Check that hidden files are included and .gitignore isn't excluding needed files

**Q: Tests fail after setup?**
A: Install textual: `pip install textual>=0.47.0`

---

## Summary

You now have a clean repository with:
- ✅ All Phase 1-5 code
- ✅ 63 passing tests
- ✅ Complete documentation
- ✅ No git history corruption
- ✅ Ready for Phase 6 development

**Time to complete**: ~5 minutes
**Result**: Production-ready Release 01

---

**Need help?** Check `NEW-REPO-INSTRUCTIONS.md` for detailed instructions or `RELEASE-01-SUMMARY.md` for complete feature documentation.
