# Run from a clone: powershell -ExecutionPolicy Bypass -File install.ps1 [options]
$ErrorActionPreference = 'Stop'
$uv = Get-Command uv -ErrorAction SilentlyContinue
$localUv = Join-Path $HOME '.local\bin\uv.exe'
if (-not $uv -and (Test-Path $localUv)) { $uv = Get-Item $localUv }
if (-not $uv) {
  Write-Host 'Installing uv from its official installer.'
  $env:UV_NO_MODIFY_PATH = '1'
  $script = Join-Path ([IO.Path]::GetTempPath()) ([IO.Path]::GetRandomFileName() + '.ps1')
  try {
    Invoke-WebRequest https://astral.sh/uv/install.ps1 -OutFile $script
    & powershell -ExecutionPolicy Bypass -File $script
    if ($LASTEXITCODE -ne 0) { throw 'uv bootstrap failed' }
  } finally { Remove-Item $script -ErrorAction SilentlyContinue }
  $exe = Join-Path $HOME '.local\bin\uv.exe'
  if (-not (Test-Path $exe)) { throw 'uv install not found; inspect installer output' }
} else { $exe = if ($uv.Source) { $uv.Source } else { $uv.FullName }; Write-Host 'uv already installed; skipped.' }
$shared = Join-Path $PSScriptRoot 'scripts/install.py'
$downloaded = $false
if (-not (Test-Path $shared)) {
  $shared = Join-Path ([IO.Path]::GetTempPath()) ([IO.Path]::GetRandomFileName() + '.py')
  Invoke-WebRequest https://raw.githubusercontent.com/Harsh23Kashyap/customchat/main/scripts/install.py -OutFile $shared
  $downloaded = $true
}
if ($args -contains '--offline') { $env:UV_OFFLINE = '1' }
try {
  & $exe run --no-project --python 3.12 $shared --uv $exe @args
  $code = $LASTEXITCODE
} finally { if ($downloaded) { Remove-Item $shared -ErrorAction SilentlyContinue } }
exit $code
