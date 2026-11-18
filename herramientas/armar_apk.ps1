# Arma la app de Android firmada: dist\ControlCelular.apk
#
# Usa las herramientas de %LOCALAPPDATA%\ControlCelular-herramientas (Java 17, SDK de Android, Gradle), fuera del
# proyecto. La firma de la app también vive ahí (firma\): HAY QUE GUARDARLA. Si se pierde, la próxima versión se
# firma con otra y Android no deja actualizar: hay que desinstalar la app y perder sus datos.
# Nunca va al repo (es privada).

$ErrorActionPreference = "Stop"
$raiz = Split-Path -Parent $PSScriptRoot
$H = Join-Path $env:LOCALAPPDATA "ControlCelular-herramientas"
$jdk = Get-ChildItem $H -Directory -Filter "jdk-17*" -ErrorAction SilentlyContinue | Select-Object -First 1
if (-not $jdk -or -not (Test-Path "$H\sdk\platforms")) {
    Write-Host "  Faltan las herramientas de Android en $H (Java 17 + SDK). Sin eso no se puede armar la app."
    exit 1
}
$env:JAVA_HOME = $jdk.FullName
$env:ANDROID_HOME = "$H\sdk"
$env:CONTROL_ARMADO_ANDROID = "$H\armado-android"

# Firma: se crea una sola vez (clave al azar) y se reutiliza siempre
$firma = "$H\firma"
$props = "$firma\firma.properties"
if (-not (Test-Path $props)) {
    New-Item -ItemType Directory -Force $firma | Out-Null
    $clave = -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 32 | ForEach-Object { [char]$_ })
    $almacen = "$firma\controlcelular.jks"
    & "$env:JAVA_HOME\bin\keytool.exe" -genkeypair -keystore $almacen -alias controlcelular -keyalg RSA -keysize 2048 `
        -validity 36500 -storepass $clave -keypass $clave -dname "CN=Control Celular, O=WorkOn2027" | Out-Null
    $archivo = $almacen -replace '\\', '/'
    Set-Content $props -Encoding ascii -Value @("archivo=$archivo", "alias=controlcelular", "clave=$clave")
    Write-Host "  Firma nueva creada en $firma (guardala: sin ella no se puede actualizar la app)."
}
$env:CONTROL_FIRMA = $props

# Dónde está el SDK (local.properties no va al repo)
$sdk = ("$H\sdk" -replace '\\', '/')
Set-Content "$raiz\android\local.properties" -Encoding ascii -Value "sdk.dir=$sdk"

Push-Location "$raiz\android"
try {
    & .\gradlew.bat --no-daemon --quiet --project-cache-dir "$H\cache-android" assembleRelease
    if ($LASTEXITCODE -ne 0) { throw "Falló el armado de la app de Android." }
} finally {
    Pop-Location
}
$apk = "$H\armado-android\app\outputs\apk\release\app-release.apk"
New-Item -ItemType Directory -Force "$raiz\dist" | Out-Null
Copy-Item $apk "$raiz\dist\ControlCelular.apk" -Force
Write-Host ("  App de Android: dist\ControlCelular.apk ({0:N1} MB)" -f ((Get-Item "$raiz\dist\ControlCelular.apk").Length / 1MB))
