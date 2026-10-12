$ErrorActionPreference = 'Stop'
$launcher = Join-Path $PSScriptRoot '../manage.ps1'
function docker {
    $global:LASTEXITCODE = 0
    $call = $args -join ' '
    $global:observedCalls.Add($call)
    if ($call -eq 'version' -and $global:scenario -eq 'denied') { $global:LASTEXITCODE = 1; return }
    if ($call -eq 'ps -aq --filter name=^/moriq-webui$' -and $global:scenario -in @('conflict', 'owned', 'unlabeled')) { 'existing-id'; return }
    if ($call -like 'inspect *') {
        if ($call -ne 'inspect --format {{json .Config.Labels}} moriq-webui') { throw 'Use a quote-free Docker JSON template for Windows PowerShell.' }
        if ($global:scenario -eq 'owned') { '{"com.docker.compose.project":"moriq-local","com.docker.compose.service":"open-webui"}' }
        elseif ($global:scenario -eq 'unlabeled') { 'null' }
        else { '{"com.docker.compose.project":"unrelated","com.docker.compose.service":"open-webui"}' }
        return
    }
    if ($call -eq 'volume ls --format {{.Name}}' -and $global:scenario -in @('existing-volume', 'owned')) { 'moriq-webui-data'; return }
}
function Get-PSDrive {
    [pscustomobject]@{ Free = $(if ($global:scenario -eq 'disk-full') { 64MB } else { 20GB }) }
}
function Get-NetTCPConnection {
    if ($global:scenario -eq 'port-conflict') { [pscustomobject]@{ LocalPort = 3000 } }
}
function Invoke-RestMethod { [pscustomobject]@{ status = $true } }
function Invoke-WebRequest { [pscustomobject]@{ StatusCode = 200 } }
foreach ($case in @('denied', 'conflict', 'unlabeled', 'disk-full', 'port-conflict', 'existing-volume', 'new-volume', 'owned')) {
    $global:scenario = $case
    $global:observedCalls = [Collections.Generic.List[string]]::new()
    $failure = $null
    try { & $launcher Start } catch { $failure = $_.Exception.Message }
    $mutations = @($global:observedCalls | Where-Object { $_ -match 'volume create| pull$| up | stop$| restart$' })
    if ($case -eq 'new-volume') {
        if ($failure -or $mutations.Count -ne 3) { throw "New-volume path failed: $failure / $mutations" }
        if (-not ($mutations[-1] -match '--no-recreate --wait')) { throw 'Missing no-recreate/health wait' }
    } elseif ($case -eq 'owned') {
        if ($failure -or $mutations.Count -ne 1 -or $mutations[0] -notmatch '--no-recreate --wait') { throw "Existing owned container path failed: $failure / $mutations" }
    } elseif (-not $failure -or $mutations.Count -ne 0) {
        throw "Guard failed: $case / $failure / $mutations"
    }
    Write-Host "PASS (mock only): $case"
}
