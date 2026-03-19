$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$InstallDir = "$env:USERPROFILE\.local\bin"

if (-not (Test-Path $InstallDir)) {
    New-Item -ItemType Directory -Path $InstallDir | Out-Null
}

Copy-Item "$ScriptDir\scht.exe" "$InstallDir\scht.exe" -Force

Write-Host "scht installed to $InstallDir\scht.exe"
Write-Host "Add $InstallDir to your PATH if it is not already there."
