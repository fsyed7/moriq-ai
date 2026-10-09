$ErrorActionPreference = 'Stop'
$launcher = Join-Path $PSScriptRoot '../manage.ps1'
function docker {
    $global:LASTEXITCODE = 0
    $call = $args -join ' '
    $global:observedCalls.Add($call)
    if ($call -eq 'version' -and $global:scenario -eq 'denied') { $global:LASTEXITCODE = 1; return }
    if ($call -eq 'ps -aq --filter name=^/moriq-webui$' -and $global:scenario -eq 'conflict') { 'existing-id'; return }
    if ($call -like 'inspect *') { 'unrelated'; return }
    if ($call -eq 'volume ls --format {{.Name}}' -and $global:scenario -eq 'existing-volume') { 'moriq-webui-data'; return }
}
function Get-PSDrive {
    [pscustomobject]@{ Free = $(if ($global:scenario -eq 'disk-full') { 64MB } else { 20GB }) }
}
function Get-NetTCPConnection {
    if ($global:scenario -eq 'port-conflict') { [pscustomobject]@{ LocalPort = 3000 } }
}
function Invoke-RestMethod { [pscustomobject]@{ status = $true } }
function Invoke-WebRequest { [pscustomobject]@{ StatusCode = 200 } }
foreach ($case in @('denied', 'conflict', 'disk-full', 'port-conflict', 'existing-volume', 'new-volume')) {
    $global:scenario = $case
    $global:observedCalls = [Collections.Generic.List[string]]::new()
    $failure = $null
    try { & $launcher Start } catch { $failure = $_.Exception.Message }
    $mutations = @($global:observedCalls | Where-Object { $_ -match 'volume create| pull$| up | stop$| restart$' })
    if ($case -eq 'new-volume') {
        if ($failure -or $mutations.Count -ne 3) { throw "New-volume path failed: $failure / $mutations" }
        if (-not ($mutations[-1] -match '--no-recreate --wait')) { throw 'Missing no-recreate/health wait' }
    } elseif (-not $failure -or $mutations.Count -ne 0) {
        throw "Guard failed: $case / $failure / $mutations"
    }
    Write-Host "PASS (mock only): $case"
}
