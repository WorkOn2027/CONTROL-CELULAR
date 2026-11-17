# Borra versiones viejas de Control Celular que ya no sirven (lo corre el instalador, si la casilla está marcada).
#
#  - Instaladores y versiones portátiles viejas en Descargas y en el Escritorio. SOLO estos nombres exactos:
#      ControlCelular.exe, ControlCelular (2).exe, ControlCelular-Instalar-<versión>.exe, ControlCelular-Instalar-<versión> (2).exe
#    Nunca borra el instalador que se está usando ahora (-Actual).
#  - Restos temporales de la versión portátil (%TEMP%\_MEI...): solo si adentro está la página de Control Celular
#    y el instalador de ViGEmBus, o sea, si seguro son de Control Celular. Si alguno está en uso, se deja.
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
        (Test-Path -LiteralPath (Join-Path $_.FullName "web\index.html")) -and
        (Get-ChildItem -LiteralPath (Join-Path $_.FullName "terceros") -Filter "ViGEmBus_*.exe")
    } | ForEach-Object {
        Remove-Item -LiteralPath $_.FullName -Recurse -Force
        if (-not (Test-Path -LiteralPath $_.FullName)) { $borrados++; Write-Output "borrado: $($_.FullName)" }
    }
}
Write-Output "total: $borrados"
