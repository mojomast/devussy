# Start DevUssY Backend Server
# Run this from anywhere, it will set up paths correctly

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent (Split-Path -Parent $scriptDir)

Write-Host "Starting DevUssY Backend Server..." -ForegroundColor Cyan
Write-Host "Project Root: $projectRoot" -ForegroundColor Gray
Write-Host "Backend Dir: $scriptDir" -ForegroundColor Gray
Write-Host ""

# Set environment variables
$env:REQUESTY_API_KEY = "rqsty-sk-kKVdK6q/TFmlnhkmyj6p9q3U6d4t+GbdljCvLMc3z6JpR1m5O6CRdlxnnHQLbflco5WKmFiVHhHKY3MWpHTRraW69Icbm+qJnY2YglxxEgY="
$env:PYTHONPATH = $projectRoot

# Change to streaming_server directory
Set-Location $scriptDir

Write-Host "Starting uvicorn on http://127.0.0.1:8000" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop" -ForegroundColor Gray
Write-Host ""

# Start uvicorn
python -m uvicorn app:app --reload --port 8000
