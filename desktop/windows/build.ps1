param(
    [Parameter(Mandatory=$true)][string]$MsysRoot,
    [Parameter(Mandatory=$true)][string]$Work
)
$ErrorActionPreference = 'Stop'
function Invoke-Native([scriptblock]$Command) {
    & $Command
    if ($LASTEXITCODE -ne 0) { throw "Build failed (exit $LASTEXITCODE)" }
}
$workPath = (New-Item -ItemType Directory -Path $Work -Force).FullName
$engine = Join-Path $workPath 'engine'
if (Test-Path $engine) { throw "Use a new work directory for a reproducible checkout" }
Invoke-Native { git -c core.autocrlf=false clone --branch v1.10.0 --depth 1 https://github.com/chiaki-ng/chiaki-ng $engine }
Push-Location $engine
try {
    if ((git rev-parse HEAD) -ne '0c4a45df0cae2af2ba2daef84e881850b07038a3') { throw 'Unexpected engine revision' }
    Invoke-Native { git -c core.autocrlf=false submodule update --init --recursive }
    Invoke-Native { git apply --whitespace=nowarn "$PSScriptRoot/engine.patch" }
    Copy-Item "$PSScriptRoot/*.h" gui/include
    Copy-Item "$PSScriptRoot/deckivo.ico" gui
    $desktop = Join-Path $PSScriptRoot '../linux'
    Copy-Item "$desktop/deckivo.svg","$desktop/assets/ps5-console.png","$desktop/assets/fonts/IBMPlexSans.ttf" gui/src/qml
    Copy-Item "$PSScriptRoot/engine-ru.json" gui/src/qml
    Copy-Item "$desktop/assets/desktop-translations.json","$desktop/assets/update-public.der","$desktop/assets/support/kofi.svg" gui/src/qml
    $artwork = "$desktop/assets/controller-lab/media/remteh-gamepad"
    Copy-Item "$artwork/v20261011/tools/gamepad-test/artwork/dualsense-front.png","$artwork/ds4-20261011a/tools/gamepad-test/artwork/dualshock-4-front.png","$artwork/xbox-20261011a/tools/gamepad-test/artwork/xbox-series-front.png" gui/src/qml
    Copy-Item "$PSScriptRoot/../../docs/guides" gui/src/qml/guides -Recurse
    $env:MSYSTEM = 'UCRT64'
    $env:CHERE_INVOKING = '1'
    $env:DECKIVO_SCRIPTS = $PSScriptRoot
    Invoke-Native { & "$MsysRoot/usr/bin/bash.exe" -lc 'bash "$(cygpath -u "$DECKIVO_SCRIPTS")/install-qt.sh" && bash "$(cygpath -u "$DECKIVO_SCRIPTS")/configure.sh"' }
} finally { Pop-Location }
