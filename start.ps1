# Run from a clone: powershell -ExecutionPolicy Bypass -File install.ps1 [options]
$ErrorActionPreference = 'Stop'
$uv = Get-Command uv -ErrorAction SilentlyContinue
$localUv = Join-Path $HOME '.local\bin\uv.exe'
if (-not $uv -and (Test-Path $localUv)) { $uv = Get-Item $localUv }
if (-not $uv) {
  Write-Host 'Installing uv from its official installer.'
  $env:UV_NO_MODIFY_PATH = '1'
  $env:UV_INSTALL_DIR = Join-Path $HOME '.local\bin'
  $script = Join-Path ([IO.Path]::GetTempPath()) ([IO.Path]::GetRandomFileName() + '.ps1')
  try {
    Invoke-WebRequest https://astral.sh/uv/install.ps1 -OutFile $script
    # Keep the same engine as this script, rather than crossing pwsh/WindowsPowerShell module paths.
    $engine = Join-Path $PSHOME $(if ($PSVersionTable.PSEdition -eq 'Core') { 'pwsh.exe' } else { 'powershell.exe' })
    # Inherited PS7 module paths can shadow WindowsPowerShell's built-in Security module.
    $savedModulePath = $env:PSModulePath
    try {
      $env:PSModulePath = Join-Path $PSHOME 'Modules'
      & $engine -NoProfile -ExecutionPolicy Bypass -File $script
    } finally { $env:PSModulePath = $savedModulePath }
    if ($LASTEXITCODE -ne 0) { throw 'uv bootstrap failed' }
  } finally { Remove-Item $script -ErrorAction SilentlyContinue }
  $exe = Join-Path $HOME '.local\bin\uv.exe'
  if (-not (Test-Path $exe)) { throw 'uv install not found; inspect installer output' }
} else { $exe = if ($uv.Source) { $uv.Source } else { $uv.FullName }; Write-Host 'uv already installed; skipped.' }
# uv tool run is uvx; the published package needs no Git installation.
$source = if ($env:CUSTOMCHAT_INSTALL_SOURCE) { $env:CUSTOMCHAT_INSTALL_SOURCE } else { 'customchat-app==0.1.3' }
Remove-Item Env:PYTHONPATH -ErrorAction SilentlyContinue
Remove-Item Env:PYTHONHOME -ErrorAction SilentlyContinue
& $exe tool run --python 3.12 --from $source customchat start @args
exit $LASTEXITCODE
