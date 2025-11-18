# Start DevUssyFresh backend with environment variables loaded
# This script loads .env and .env.local files and starts the backend

Write-Host "Starting DevUssyFresh backend..." -ForegroundColor Green

# Load .env file if it exists
if (Test-Path ".env") {
    Write-Host "Loading .env file..." -ForegroundColor Cyan
    Get-Content ".env" | ForEach-Object {
        if ($_ -match '^\s*([^#][^=]*)\s*=\s*(.*)$') {
            $name = $matches[1].Trim()
            $value = $matches[2].Trim()
            [Environment]::SetEnvironmentVariable($name, $value, "Process")
            Write-Host "  Set $name" -ForegroundColor Gray
        }
    }
}

# Load .env.local file if it exists (overrides .env)
if (Test-Path ".env.local") {
    Write-Host "Loading .env.local file..." -ForegroundColor Cyan
    Get-Content ".env.local" | ForEach-Object {
        if ($_ -match '^\s*([^#][^=]*)\s*=\s*(.*)$') {
            $name = $matches[1].Trim()
            $value = $matches[2].Trim()
            [Environment]::SetEnvironmentVariable($name, $value, "Process")
            Write-Host "  Set $name" -ForegroundColor Gray
        }
    }
} else {
    Write-Host "Warning: .env.local not found. Create one with your REQUESTY_API_KEY!" -ForegroundColor Yellow
}

# Verify critical environment variables
Write-Host "`nVerifying configuration..." -ForegroundColor Cyan
$apiKey = [Environment]::GetEnvironmentVariable("REQUESTY_API_KEY", "Process")
if ($apiKey) {
    $maskedKey = $apiKey.Substring(0, [Math]::Min(8, $apiKey.Length)) + "..."
    Write-Host "  REQUESTY_API_KEY: $maskedKey" -ForegroundColor Green
} else {
    Write-Host "  REQUESTY_API_KEY: NOT SET!" -ForegroundColor Red
}

$detourEnabled = [Environment]::GetEnvironmentVariable("DETOUR_ENABLED", "Process")
Write-Host "  DETOUR_ENABLED: $detourEnabled" -ForegroundColor $(if ($detourEnabled -eq "true") { "Green" } else { "Yellow" })

$instrEnabled = [Environment]::GetEnvironmentVariable("DETOUR_INSTRUMENTATION_ENABLED", "Process")
Write-Host "  DETOUR_INSTRUMENTATION_ENABLED: $instrEnabled" -ForegroundColor $(if ($instrEnabled -eq "true") { "Green" } else { "Yellow" })

$metaEnabled = [Environment]::GetEnvironmentVariable("DETOUR_METADATA_LOGGING_ENABLED", "Process")
Write-Host "  DETOUR_METADATA_LOGGING_ENABLED: $metaEnabled" -ForegroundColor $(if ($metaEnabled -eq "true") { "Green" } else { "Yellow" })

# Start the backend
Write-Host "`nStarting backend server..." -ForegroundColor Green
$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
[Console]::InputEncoding  = [System.Text.UTF8Encoding]::new()
python -m src.web.app
