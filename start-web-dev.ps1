# Quick Start - Web Interface Development

# This script helps you get started with the web interface development
# Run from the project root directory

Write-Host "🚀 DevPlan Orchestrator - Web Interface Quick Start" -ForegroundColor Cyan
Write-Host ""

# Check Python version
Write-Host "📌 Checking Python version..." -ForegroundColor Yellow
$pythonVersion = python --version
Write-Host "   $pythonVersion" -ForegroundColor Green

# Check if virtual environment is activated
if (-not $env:VIRTUAL_ENV) {
    Write-Host "⚠️  Virtual environment not activated" -ForegroundColor Yellow
    Write-Host "   Run: .\venv\Scripts\Activate.ps1" -ForegroundColor White
    Write-Host ""
}

# Install Python dependencies
Write-Host "📦 Installing Python dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt --quiet
Write-Host "   ✅ Python dependencies installed" -ForegroundColor Green
Write-Host ""

# Check if frontend dependencies are installed
Write-Host "📦 Checking frontend setup..." -ForegroundColor Yellow
$frontendPath = "frontend"

if (Test-Path "$frontendPath\node_modules") {
    Write-Host "   ✅ Frontend dependencies already installed" -ForegroundColor Green
} else {
    Write-Host "   📥 Installing frontend dependencies (this may take a minute)..." -ForegroundColor Yellow
    Push-Location $frontendPath
    npm install --silent
    Pop-Location
    Write-Host "   ✅ Frontend dependencies installed" -ForegroundColor Green
}
Write-Host ""

# Check environment variables
Write-Host "🔑 Checking environment variables..." -ForegroundColor Yellow
if (-not $env:OPENAI_API_KEY) {
    Write-Host "   ⚠️  OPENAI_API_KEY not set" -ForegroundColor Yellow
    Write-Host "   Set it with: `$env:OPENAI_API_KEY = 'your-key-here'" -ForegroundColor White
} else {
    Write-Host "   ✅ OPENAI_API_KEY is set" -ForegroundColor Green
}
Write-Host ""

# Display next steps
Write-Host "🎯 Next Steps:" -ForegroundColor Cyan
Write-Host ""
Write-Host "1️⃣  Start the backend (FastAPI):" -ForegroundColor White
Write-Host "   python -m src.web.app" -ForegroundColor Yellow
Write-Host "   Then visit: http://localhost:8000/docs" -ForegroundColor Gray
Write-Host ""
Write-Host "2️⃣  In a new terminal, start the frontend (React):" -ForegroundColor White
Write-Host "   cd frontend" -ForegroundColor Yellow
Write-Host "   npm run dev" -ForegroundColor Yellow
Write-Host "   Then visit: http://localhost:3000" -ForegroundColor Gray
Write-Host ""
Write-Host "📚 Documentation:" -ForegroundColor Cyan
Write-Host "   - WEB_INTERFACE_GUIDE.md - Complete setup guide" -ForegroundColor White
Write-Host "   - WEB_INTERFACE_SUMMARY.md - Session summary with examples" -ForegroundColor White
Write-Host "   - devplan.md - Phase 11 roadmap" -ForegroundColor White
Write-Host ""
Write-Host "🏗️  What needs to be built:" -ForegroundColor Cyan
Write-Host "   - Frontend components (Layout, HomePage, CreateProjectPage, etc.)" -ForegroundColor White
Write-Host "   - Project creation form (multi-step wizard)" -ForegroundColor White
Write-Host "   - Real-time streaming UI (WebSocket connection)" -ForegroundColor White
Write-Host "   - File viewer with markdown rendering" -ForegroundColor White
Write-Host ""
Write-Host "✨ You're all set! Happy coding! 🎨" -ForegroundColor Green
