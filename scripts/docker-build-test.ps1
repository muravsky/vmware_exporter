# Build (and optionally push) a non-latest Docker Hub test image.
#
# Examples:
#   .\scripts\docker-build-test.ps1
#   .\scripts\docker-build-test.ps1 -Tag dev-modernization
#   .\scripts\docker-build-test.ps1 -Tag dev-modernization -Push
#   .\scripts\docker-build-test.ps1 -Tag dev-modernization -Platform linux/amd64 -Push

param(
    [string]$Image = "muravsky/vmware-exporter",
    [string]$Tag = "dev-$(Get-Date -Format 'yyyyMMdd')",
    [string]$Platform = "",
    [switch]$Push
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

$fullTag = "${Image}:${Tag}"

Write-Host "Building test image: $fullTag"

if ($Platform) {
    if ($Push) {
        docker buildx build --platform $Platform -t $fullTag --push .
    } else {
        docker buildx build --platform $Platform -t $fullTag --load .
    }
} else {
    docker build -t $fullTag .
}

if (-not $Push) {
    Write-Host ""
    Write-Host "Built locally. Run side-by-side with production latest:"
    Write-Host "  docker run -d --name vmware_exporter_old -p 9272:9272 ... ${Image}:latest"
    Write-Host "  docker run -d --name vmware_exporter_new -p 9273:9272 ... $fullTag"
    Write-Host ""
    Write-Host "To push this test tag (without touching latest):"
    Write-Host "  .\scripts\docker-build-test.ps1 -Tag $Tag -Push"
    exit 0
}

Write-Host ""
Write-Host "Pushed: $fullTag"
Write-Host "Pull and run on another host:"
Write-Host "  docker pull $fullTag"
Write-Host "  docker run -d --name vmware_exporter_test -p 9273:9272 ... $fullTag"
