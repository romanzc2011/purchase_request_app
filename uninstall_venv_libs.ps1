$FileBase = $PSScriptRoot
$UninstallFile = (Join-Path $FileBase "not_requirement.txt")

if (-not $UninstallFile) {
    Write-Host "File does not exist"
    exit 1
}

$fileLibs = Get-Content -Path $UninstallFile -Raw
$fileLibs = $fileLibs.Replace(" ", ",")

Write-Host $fileLibs

