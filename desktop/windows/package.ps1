param(
    [Parameter(Mandatory=$true)][string]$Engine,
    [Parameter(Mandatory=$true)][string]$MsysRoot,
    [Parameter(Mandatory=$true)][string]$Destination,
    [Parameter(Mandatory=$true)][string]$Iscc,
    [string]$Python = 'python'
)
$ErrorActionPreference = 'Stop'
$prefix = (Resolve-Path "$MsysRoot/ucrt64").Path
$repo = (Resolve-Path "$PSScriptRoot/../..").Path
$enginePath = (Resolve-Path $Engine).Path
if (Test-Path -LiteralPath $Destination) { throw 'Choose a new packaging directory' }
$dir = (New-Item -ItemType Directory -Path $Destination).FullName
$stage = (New-Item -ItemType Directory -Path "$dir/stage/Deckivo" -Force).FullName
$priorPath = $env:PATH
try {
    $env:PATH = "$prefix/bin;$priorPath"
    Copy-Item "$enginePath/build/gui/Deckivo.exe" $stage
    & "$prefix/bin/windeployqt.exe" --release --qmldir "$enginePath/gui/src/qml" "$stage/Deckivo.exe"
    if ($LASTEXITCODE) { throw 'Qt deployment failed' }
    Copy-Item "$PSScriptRoot/qt.conf","$PSScriptRoot/deckivo.ico","$prefix/bin/SDL3.dll" $stage -Force
    & $Python "$PSScriptRoot/collect_dlls.py" $stage $prefix
    if ($LASTEXITCODE) { throw 'DLL collection failed' }
    Copy-Item "$repo/desktop/linux/assets/controller-lab" $stage -Recurse
    Copy-Item "$prefix/share/licenses" $stage -Recurse
    Copy-Item "$repo/COPYING" "$stage/licenses/Deckivo.txt"
    Copy-Item "$enginePath/COPYING" "$stage/licenses/chiaki-ng.txt"
    Copy-Item "$repo/desktop/linux/assets/fonts/OFL.txt" "$stage/licenses"
    & "$env:SystemRoot/System32/tar.exe" -acf "$dir/Deckivo-0.9.0-preview-Windows-x64-Portable.zip" -C "$dir/stage" Deckivo
    if ($LASTEXITCODE) { throw 'ZIP creation failed' }
    & $Iscc "/DPayload=$stage" "/O$dir" "$PSScriptRoot/installer.iss"
    if ($LASTEXITCODE) { throw 'Installer build failed' }
} finally { $env:PATH = $priorPath }
