[CmdletBinding()]
param(
    [string]$Lang = "en",
    [switch]$Uninstall
)

$SkillsDir = if ($env:CLAUDE_SKILLS_DIR) { $env:CLAUDE_SKILLS_DIR } else { [Environment]::GetFolderPath('MyDocuments') }
$Repo = "abrahambahez/loretools"

if ($Uninstall) {
    Get-ChildItem -Path $SkillsDir -Filter "loretools-*-$Lang-*.zip" -ErrorAction SilentlyContinue |
        Remove-Item -Force
    Write-Host "Uninstalled loretools skills from $SkillsDir"
    exit 0
}

$Release = Invoke-RestMethod "https://api.github.com/repos/$Repo/releases/latest"
$Assets = $Release.assets | Where-Object { $_.name -like "loretools-*-$Lang-*.zip" }

if (-not $Assets) {
    Write-Error "No skills assets found for language '$Lang'"
    exit 1
}

New-Item -ItemType Directory -Path $SkillsDir -Force | Out-Null

foreach ($asset in $Assets) {
    $dest = Join-Path $SkillsDir $asset.name
    Invoke-WebRequest -Uri $asset.browser_download_url -OutFile $dest
    Write-Host "Downloaded: $($asset.name) -> $SkillsDir"
}
