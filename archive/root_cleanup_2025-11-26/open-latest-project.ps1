# Open Latest Generated Project
# Quick script to open the most recently generated project folder

$docsPath = "docs"

# Get all timestamped project folders
$projectFolders = Get-ChildItem -Path $docsPath -Directory | 
    Where-Object { $_.Name -match "_\d{8}_\d{6}$" } |
    Sort-Object Name -Descending

if ($projectFolders.Count -eq 0) {
    Write-Host "❌ No generated project folders found in $docsPath" -ForegroundColor Red
    Write-Host "   Run 'devussy interactive-design' to create a project" -ForegroundColor Yellow
    exit 1
}

$latestFolder = $projectFolders[0]

Write-Host "📁 Opening latest project:" -ForegroundColor Cyan
Write-Host "   $($latestFolder.FullName)" -ForegroundColor White
Write-Host ""

# Open in File Explorer
explorer $latestFolder.FullName

# Also list the markdown files
Write-Host "📄 Files in project:" -ForegroundColor Green
Get-ChildItem -Path $latestFolder.FullName -Filter "*.md" | ForEach-Object {
    $size = [math]::Round($_.Length / 1KB, 2)
    Write-Host "   - $($_.Name) ($size KB)" -ForegroundColor Gray
}

Write-Host ""
Write-Host "💡 Tip: To open the devplan:" -ForegroundColor Yellow
Write-Host "   code `"$($latestFolder.FullName)\devplan.md`"" -ForegroundColor Gray
