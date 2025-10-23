# DevUssY Development Startup Script
# Starts both backend and frontend with development settings

Write-Host "🚀 Starting DevUssY Development Environment..." -ForegroundColor Cyan
Write-Host ""

# Set development mode (disables encryption)
$env:DEVUSSY_DEV_MODE = 'true'
Write-Host "✅ Development mode enabled (encryption disabled)" -ForegroundColor Green

# Check if backend is already running
$backendRunning = Get-Process -Name python -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like '*uvicorn*' }
if ($backendRunning) {
    Write-Host "⚠️  Backend appears to be running already (port 8000)" -ForegroundColor Yellow
    $response = Read-Host "Kill and restart? (y/n)"
    if ($response -eq 'y') {
        Stop-Process -Id $backendRunning.Id -Force
        Start-Sleep -Seconds 2
    }
}

# Start backend in new window
Write-Host "🔧 Starting backend on http://localhost:8000..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList @(
    '-NoExit',
    '-Command',
    "cd '$PWD'; `$env:DEVUSSY_DEV_MODE='true'; python -m uvicorn src.web.app:app --host 127.0.0.1 --port 8000 --reload"
)

# Wait for backend to start
Write-Host "⏳ Waiting for backend to initialize..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

# Start frontend in new window
Write-Host "🎨 Starting frontend..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList @(
    '-NoExit',
    '-Command',
    "cd '$PWD\frontend'; npm run dev"
)

Write-Host ""
Write-Host "✅ Development environment starting!" -ForegroundColor Green
Write-Host ""
Write-Host "📡 Backend API:  http://localhost:8000" -ForegroundColor White
Write-Host "🌐 Frontend UI:  http://localhost:3000 (or 3001 if 3000 is taken)" -ForegroundColor White
Write-Host ""
Write-Host "💡 Tip: Both servers will auto-reload on file changes" -ForegroundColor Gray
Write-Host "🔓 Development mode: API keys stored in plaintext (faster debugging)" -ForegroundColor Gray
Write-Host ""
Write-Host "Press Ctrl+C in each terminal window to stop the servers." -ForegroundColor Gray
