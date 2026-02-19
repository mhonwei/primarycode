$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

$nodeDir = Join-Path $PSScriptRoot ".." "node_portable"
$zipFile = Join-Path $nodeDir "node.zip"

if (!(Test-Path $nodeDir)) { New-Item -ItemType Directory -Path $nodeDir | Out-Null }

$urls = @(
    "https://npmmirror.com/mirrors/node/v20.11.0/node-v20.11.0-win-x64.zip",
    "https://nodejs.org/dist/v20.11.0/node-v20.11.0-win-x64.zip"
)

$downloaded = $false
foreach ($url in $urls) {
    Write-Host "  Downloading from: $url"
    try {
        Invoke-WebRequest -Uri $url -OutFile $zipFile -TimeoutSec 300
        $downloaded = $true
        break
    } catch {
        Write-Host "  Failed, trying next source..."
    }
}

if (!$downloaded) {
    Write-Host "ERROR: Download failed"
    exit 1
}

Write-Host "  Extracting Node.js..."
Expand-Archive -Path $zipFile -DestinationPath $nodeDir -Force
Remove-Item $zipFile -Force

Write-Host "  Done."
