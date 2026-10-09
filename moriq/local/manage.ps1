[CmdletBinding()]
param(
    [ValidateSet('Check', 'Start', 'Stop', 'Restart', 'Status')]
    [string]$Action = 'Check',
    [switch]$ReviewedExistingData
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$composeFile = Join-Path $repoRoot 'compose.local.yaml'
$composeArgs = @('compose', '--project-name', 'moriq-local', '-f', $composeFile)

function Invoke-Docker {
    param([string[]]$DockerArgs)
    & docker @DockerArgs
    if ($LASTEXITCODE -ne 0) { throw "Docker command failed: $($DockerArgs -join ' ')" }
}

function Confirm-LocalResponse {
    $ready = Invoke-RestMethod 'http://127.0.0.1:3000/ready' -TimeoutSec 15
    if ($ready.status -ne $true) { throw 'Application is not ready.' }
    $page = Invoke-WebRequest 'http://127.0.0.1:3000/' -UseBasicParsing -TimeoutSec 15
    if ($page.StatusCode -ne 200) { throw 'Application page did not return HTTP 200.' }
    Write-Host 'Open WebUI responds at http://127.0.0.1:3000. Model inference is a separate check.'
}

Invoke-Docker -DockerArgs @('version')
Invoke-Docker -DockerArgs ($composeArgs + @('config', '--quiet'))
$containerIds = @(Invoke-Docker -DockerArgs @('ps', '-aq', '--filter', 'name=^/moriq-webui$'))
$owned = $false
if ($containerIds.Count -gt 0) {
    $project = Invoke-Docker -DockerArgs @('inspect', '--format', '{{ index .Config.Labels "com.docker.compose.project" }}', 'moriq-webui')
    $service = Invoke-Docker -DockerArgs @('inspect', '--format', '{{ index .Config.Labels "com.docker.compose.service" }}', 'moriq-webui')
    $owned = ($project -eq 'moriq-local' -and $service -eq 'open-webui')
}

if ($Action -eq 'Check') {
    Invoke-Docker -DockerArgs @('ps', '-a')
    Invoke-Docker -DockerArgs @('image', 'ls', 'ghcr.io/open-webui/open-webui')
    Invoke-Docker -DockerArgs @('volume', 'ls')
    Get-PSDrive -PSProvider FileSystem | Select-Object Name, Used, Free
    Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue |
        Where-Object LocalPort -eq 3000 | Select-Object LocalAddress, LocalPort, OwningProcess
    if ($containerIds.Count -gt 0 -and -not $owned) {
        Write-Warning 'moriq-webui exists outside this Compose project. Review it; do not delete it.'
    }
    return
}
if ($Action -eq 'Status') {
    Invoke-Docker -DockerArgs ($composeArgs + @('ps', '-a'))
    Confirm-LocalResponse
    return
}
if ($containerIds.Count -gt 0 -and -not $owned) {
    throw 'Name conflict: preserve and review the existing moriq-webui container before continuing.'
}
if ($Action -in @('Stop', 'Restart')) {
    if (-not $owned) { throw 'No container owned by this deployment exists.' }
    if ($Action -eq 'Stop') {
        Invoke-Docker -DockerArgs ($composeArgs + @('stop'))
    } else {
        Invoke-Docker -DockerArgs ($composeArgs + @('restart'))
        Invoke-Docker -DockerArgs ($composeArgs + @('up', '-d', '--no-recreate', '--wait', '--wait-timeout', '600'))
        Confirm-LocalResponse
    }
    return
}

# Conservative local policy, not an upstream minimum. Check Docker's disk location too.
$systemDrive = Get-PSDrive -Name ($env:SystemDrive.TrimEnd(':'))
if ($systemDrive.Free -lt 10GB) {
    throw 'Less than 10 GiB free on the Windows system drive. Free approved space before pulling images.'
}
if (-not $owned) {
    $listeners = @(Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue | Where-Object LocalPort -eq 3000)
    if ($listeners.Count -gt 0) { throw 'Port 3000 is in use. Review its owner before continuing.' }
}
$volumes = @(Invoke-Docker -DockerArgs @('volume', 'ls', '--format', '{{.Name}}'))
if ($volumes -contains 'moriq-webui-data') {
    if (-not $owned -and -not $ReviewedExistingData) {
        throw 'Existing volume: back up data, preserve its secret key, check version and all consumers; then use -ReviewedExistingData. See docs/LOCAL_DEPLOYMENT.md.'
    }
} else {
    Invoke-Docker -DockerArgs @('volume', 'create', 'moriq-webui-data')
}
# No recreation or deletion: existing containers retain their image and configuration.
if (-not $owned) { Invoke-Docker -DockerArgs ($composeArgs + @('pull')) }
Invoke-Docker -DockerArgs ($composeArgs + @('up', '-d', '--no-recreate', '--wait', '--wait-timeout', '600'))
Invoke-Docker -DockerArgs ($composeArgs + @('ps'))
Confirm-LocalResponse
