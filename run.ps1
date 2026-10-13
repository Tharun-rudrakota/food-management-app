# FreshPantry Launch Script for PowerShell
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "  FreshPantry - Smart Food Inventory & Daily Management" -ForegroundColor Green
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host ""

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

$pyCmd = "py"
try {
    & py --version | Out-Null
} catch {
    $pyCmd = "python"
}

Write-Host "Launching server on http://127.0.0.1:5000 ..." -ForegroundColor Yellow
Write-Host "Demo Credentials:" -ForegroundColor Magenta
Write-Host "  Username: demo" -ForegroundColor White
Write-Host "  Password: demo123" -ForegroundColor White
Write-Host ""
Write-Host "Opening browser in 2 seconds..." -ForegroundColor Gray

Start-Process "http://127.0.0.1:5000"
& $pyCmd app.py
