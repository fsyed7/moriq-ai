# Adds MORIQ AI to the Desktop and Start menu with its icon. It installs no other software.
# Run from this folder: powershell -ExecutionPolicy Bypass -File .\install-moriq.ps1
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$launcher = (Get-Command pyw.exe -ErrorAction SilentlyContinue).Source
if (-not $launcher) { Write-Error 'Python 3.12 was not found. Install it from python.org, then run this again.'; exit 1 }
& py -3.12 --version | Out-Null
if ($LASTEXITCODE -ne 0) { Write-Error 'Python 3.12 was not found. Install it from python.org, then run this again.'; exit 1 }
$shell = New-Object -ComObject WScript.Shell
$places = @([Environment]::GetFolderPath('Desktop'), [Environment]::GetFolderPath('Programs'))
foreach ($place in $places) {
    $link = $shell.CreateShortcut((Join-Path $place 'MORIQ AI.lnk'))
    $link.TargetPath = $launcher
    $link.Arguments = '-3.12 moriq\app\launch.py'
    $link.WorkingDirectory = $root
    $link.IconLocation = (Join-Path $root 'moriq\app\web\icons\moriq.ico')
    $link.Description = 'MORIQ AI: an assistant for architects and engineers at MORIQ'
    $link.Save()
    Write-Output "Added: $($link.FullName)"
}
