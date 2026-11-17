# Borra versiones viejas de Control Celular que ya no sirven (lo corre el instalador, si la casilla está marcada).
#
#  - Instaladores y versiones portátiles viejas en Descargas y en el Escritorio. SOLO estos nombres exactos:
#      ControlCelular.exe, ControlCelular (2).exe, ControlCelular-Instalar-<versión>.exe, ControlCelular-Instalar-<versión> (2).exe
#    Nunca borra el instalador que se está usando ahora (-Actual).
#  - Restos temporales de la versión portátil (%TEMP%\_MEI...): solo si seguro son de Control Celular: la página
#    (web\index.html) y además el instalador de ViGEmBus (desde 1.4.1) o, en las versiones anteriores,
#    web\configurar.html y web\plantillas.js. Si alguno está en uso, se deja.
# No toca los ajustes ni los celulares emparejados (%LOCALAPPDATA%\ControlCelular).
#
# Para las pruebas se pueden pasar otras carpetas con -Carpetas y -Temporal.

param(
    [string]$Actual = "",
    [string[]]$Carpetas = @(),
    [string]$Temporal = $env:TEMP
)

$ErrorActionPreference = "SilentlyContinue"
# Varias carpetas en un solo texto se separan con | (un carácter que no puede aparecer en una ruta de Windows)
$Carpetas = @($Carpetas | ForEach-Object { $_ -split '\|' } | Where-Object { $_ })
if ($Carpetas.Count -eq 0) {
    $Carpetas = @(
        (New-Object -ComObject Shell.Application).NameSpace("shell:Downloads").Self.Path,
        [Environment]::GetFolderPath("Desktop")
    ) | Where-Object { $_ } | Select-Object -Unique
}
$nombre = '^ControlCelular(-Instalar-\d+(\.\d+)*)?( \(\d+\))?\.exe$'
$actual = if ($Actual) { [IO.Path]::GetFullPath($Actual) } else { "" }
$borrados = 0

foreach ($c in $Carpetas) {
    if (-not (Test-Path -LiteralPath $c)) { continue }
    Get-ChildItem -LiteralPath $c -File | Where-Object { $_.Name -match $nombre -and $_.FullName -ne $actual } |
        ForEach-Object {
            Remove-Item -LiteralPath $_.FullName -Force
            if (-not (Test-Path -LiteralPath $_.FullName)) { $borrados++; Write-Output "borrado: $($_.FullName)" }
        }
}

if ($Temporal -and (Test-Path -LiteralPath $Temporal)) {
    Get-ChildItem -LiteralPath $Temporal -Directory -Filter "_MEI*" | Where-Object {
        $web = Join-Path $_.FullName "web"
        (Test-Path -LiteralPath (Join-Path $web "index.html")) -and (
            # desde la 1.4.1: trae el instalador de ViGEmBus
            (Get-ChildItem -LiteralPath (Join-Path $_.FullName "terceros") -Filter "ViGEmBus_*.exe") -or
            # versiones anteriores: las páginas propias de Control Celular, las tres juntas
            ((Test-Path -LiteralPath (Join-Path $web "configurar.html")) -and
             (Test-Path -LiteralPath (Join-Path $web "plantillas.js")))
        )
    } | ForEach-Object {
        Remove-Item -LiteralPath $_.FullName -Recurse -Force
        if (-not (Test-Path -LiteralPath $_.FullName)) { $borrados++; Write-Output "borrado: $($_.FullName)" }
    }
}
Write-Output "total: $borrados"
