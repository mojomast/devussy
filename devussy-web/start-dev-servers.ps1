# DevUssY Local Development Server Launcher
# Starts both the FastAPI backend and Next.js frontend

Write-Host "🚀 Starting DevUssY Local Development Servers..." -ForegroundColor Cyan
Write-Host ""

# Get the script's directory
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptDir

# Set environment variables
$env:REQUESTY_API_KEY = "rqsty-sk-kKVdK6q/TFmlnhkmyj6p9q3U6d4t+GbdljCvLMc3z6JpR1m5O6CRdlxnnHQLbflco5WKmFiVHhHKY3MWpHTRraW69Icbm+qJnY2YglxxEgY="
$env:NODE_ENV = "development"

Write-Host "📍 Project Root: $projectRoot" -ForegroundColor Gray
Write-Host ""

# Start Backend (FastAPI)
Write-Host "🔧 Starting Backend (FastAPI on port 8000)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "cd '$projectRoot/devussy-web/streaming_server'; `$env:REQUESTY_API_KEY='$env:REQUESTY_API_KEY'; `$env:PYTHONPATH='$projectRoot'; python -m uvicorn app:app --reload --port 8000"
) -WindowStyle Normal

Start-Sleep -Seconds 3

# Start Frontend (Next.js)
Write-Host "⚡ Starting Frontend (Next.js on port 3000)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "cd '$scriptDir'; npm run dev"
) -WindowStyle Normal

Write-Host ""
Write-Host "✅ Servers are starting in separate windows!" -ForegroundColor Green
Write-Host ""
Write-Host "📌 URLs:" -ForegroundColor Cyan
Write-Host "   Frontend:  http://localhost:3000" -ForegroundColor White
Write-Host "   Backend:   http://localhost:8000" -ForegroundColor White
Write-Host "   API Docs:  http://localhost:8000/docs" -ForegroundColor White
Write-Host ""
Write-Host "💡 Tip: To stop servers, close the PowerShell windows or press Ctrl+C in each." -ForegroundColor Gray
Write-Host ""
Write-Host "Press any key to exit this launcher..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
