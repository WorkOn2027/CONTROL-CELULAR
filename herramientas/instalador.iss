; Instalador de Control Celular (Inno Setup 6). Lo arma construir.bat:
;   ISCC /DVersion=1.5.0 /DOrigen=<carpeta con ControlCelular.exe y _internal> herramientas\instalador.iss
;
; Con UN solo permiso de administrador deja todo listo para escanear el QR y jugar:
;   - instala el programa en "Archivos de programa" (acceso directo en el escritorio y en el menú Inicio);
;   - instala ViGEmBus (el driver del control virtual) si falta, con su instalador oficial y sin ventanas;
;   - abre el firewall SOLO para el programa y sus puertos, en redes privadas y solo para la red de casa,
;     y saca los bloqueos que Windows le haya puesto (el cartel del firewall cerrado con «Cancelar»);
;   - si la red está como «Pública», ofrece marcarla como privada (casilla, explicada).
; Al actualizar, reemplaza la versión anterior (borra antes sus archivos) y, si la casilla está marcada, borra
;   instaladores y versiones portátiles viejas de Descargas/Escritorio y restos temporales (limpiar_viejas.ps1).
;   Nunca borra los ajustes ni los celulares emparejados.
; Al desinstalar saca el firewall y el arranque con Windows. Los datos del usuario quedan, salvo que los borre.

#ifndef Version
  #define Version "0.0.0"
#endif
#ifndef Origen
  #define Origen GetEnv("TEMP") + "\ControlCelular-carpeta\ControlCelular"
#endif
#define Programa "Control Celular"
#define Exe "ControlCelular.exe"
#define ViGEm "ViGEmBus_1.22.0_x64_x86_arm64.exe"

[Setup]
AppId={{6F1C2E5A-7B3D-4C8E-9A21-C0E7A11E2025}
AppName={#Programa}
AppVersion={#Version}
AppPublisher=WorkOn2027
AppPublisherURL=https://github.com/WorkOn2027/CONTROL-CELULAR
AppSupportURL=https://github.com/WorkOn2027/CONTROL-CELULAR/issues
DefaultDirName={autopf}\{#Programa}
DefaultGroupName={#Programa}
DisableProgramGroupPage=yes
PrivilegesRequired=admin
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=..\dist
OutputBaseFilename=ControlCelular-Instalar-{#Version}
SetupIconFile=icono.ico
UninstallDisplayIcon={app}\{#Exe}
UninstallDisplayName={#Programa}
WizardStyle=modern
Compression=lzma2/max
SolidCompression=yes
LicenseFile=..\LICENSE
CloseApplications=yes
RestartApplications=no

[Languages]
Name: "es"; MessagesFile: "compiler:Languages\Spanish.isl"
Name: "en"; MessagesFile: "compiler:Default.isl"

[CustomMessages]
es.Escritorio=Crear un ícono en el escritorio
en.Escritorio=Create a desktop icon
es.Inicio=Abrir Control Celular al prender la PC (oculto, en el ícono al lado del reloj)
en.Inicio=Open Control Celular when the PC starts (hidden, in the icon next to the clock)
es.Privada=Es la red de mi casa: marcarla como privada (si no, el celular no se puede conectar)
en.Privada=It's my home network: mark it as private (otherwise the phone can't connect)
es.Grupo=Opciones:
en.Grupo=Options:
es.Driver=Instalando ViGEmBus (el control virtual)...
en.Driver=Installing ViGEmBus (the virtual controller)...
es.Firewall=Abriendo el firewall para Control Celular (solo red privada de casa)...
en.Firewall=Opening the firewall for Control Celular (private home network only)...
es.Red=Marcando la red como privada...
en.Red=Marking the network as private...
es.Limpiar=Borrar versiones viejas que ya no sirven (instaladores y versiones portátiles anteriores en Descargas y Escritorio, y restos temporales). Tus ajustes no se tocan.
es.Limpiando=Borrando versiones viejas...
es.Abrir=Abrir Control Celular ahora
en.Limpiar=Delete old versions you no longer need (previous installers and portable versions in Downloads and Desktop, and temporary leftovers). Your settings are kept.
en.Limpiando=Deleting old versions...
en.Abrir=Open Control Celular now
es.FalloDriver=No se pudo instalar ViGEmBus (código %1). Control Celular va a ofrecer instalarlo cuando lo abras.
en.FalloDriver=ViGEmBus couldn't be installed (code %1). Control Celular will offer to install it when you open it.

[Tasks]
Name: "escritorio"; Description: "{cm:Escritorio}"; GroupDescription: "{cm:Grupo}"
Name: "privada"; Description: "{cm:Privada}"; GroupDescription: "{cm:Grupo}"; Check: HayRedPublica
Name: "inicio"; Description: "{cm:Inicio}"; GroupDescription: "{cm:Grupo}"; Flags: unchecked
Name: "limpiar"; Description: "{cm:Limpiar}"; GroupDescription: "{cm:Grupo}"

[InstallDelete]
; Antes de instalar, se borran los archivos del programa de la versión anterior (no los datos del usuario).
Type: filesandordirs; Name: "{app}\_internal"

[Files]
Source: "{#Origen}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\terceros\{#ViGEm}"; DestDir: "{tmp}"; Flags: deleteafterinstall; Check: FaltaViGEm
Source: "..\terceros\LICENCIA-ViGEmBus.txt"; DestDir: "{app}\licencias"
Source: "..\LICENSE"; DestDir: "{app}\licencias"; DestName: "LICENCIA-Control-Celular.txt"
Source: "limpiar_viejas.ps1"; DestDir: "{tmp}"; Flags: deleteafterinstall

[Icons]
Name: "{group}\{#Programa}"; Filename: "{app}\{#Exe}"
Name: "{group}\{cm:UninstallProgram,{#Programa}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#Programa}"; Filename: "{app}\{#Exe}"; Tasks: escritorio

[Registry]
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "ControlCelular"; ValueData: """{app}\{#Exe}"" --minimizado"; Tasks: inicio; Flags: uninsdeletevalue

[Run]
Filename: "{app}\{#Exe}"; Description: "{cm:Abrir}"; Flags: postinstall nowait skipifsilent

[UninstallRun]
Filename: "powershell.exe"; Parameters: "-NoProfile -ExecutionPolicy Bypass -Command ""Get-NetFirewallRule -DisplayName 'CONTROL CELULAR*' -ErrorAction SilentlyContinue | Remove-NetFirewallRule"""; Flags: runhidden; RunOnceId: "SacarFirewall"
Filename: "reg.exe"; Parameters: "delete HKCU\Software\Microsoft\Windows\CurrentVersion\Run /v ControlCelular /f"; Flags: runhidden; RunOnceId: "SacarInicio"

[Code]
var
  ReiniciarPorDriver: Boolean;

function FaltaViGEm: Boolean;
begin
  Result := not RegKeyExists(HKLM, 'SYSTEM\CurrentControlSet\Services\ViGEmBus');
end;

function HayRedPublica: Boolean;
var
  Codigo: Integer;
begin
  { powershell termina con 1 si alguna red conectada está como "Pública" }
  if Exec('powershell.exe', '-NoProfile -Command "if (Get-NetConnectionProfile | Where-Object NetworkCategory -eq ''Public'') { exit 1 } else { exit 0 }"',
          '', SW_HIDE, ewWaitUntilTerminated, Codigo) then
    Result := (Codigo = 1)
  else
    Result := False;
end;

procedure CorrerPowerShell(const Orden: String);
var
  Codigo: Integer;
begin
  Exec('powershell.exe', '-NoProfile -ExecutionPolicy Bypass -Command "' + Orden + '"', '', SW_HIDE,
       ewWaitUntilTerminated, Codigo);
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  Codigo: Integer;
  Programa: String;
begin
  if CurStep <> ssPostInstall then
    Exit;

  { 1. ViGEmBus, solo si falta (instalador oficial, sin ventanas) }
  if FaltaViGEm then
  begin
    WizardForm.StatusLabel.Caption := CustomMessage('Driver');
    if Exec(ExpandConstant('{tmp}\{#ViGEm}'), '/quiet /norestart', '', SW_HIDE, ewWaitUntilTerminated, Codigo) then
    begin
      if Codigo = 3010 then
        ReiniciarPorDriver := True
      else if Codigo <> 0 then
        MsgBox(FmtMessage(CustomMessage('FalloDriver'), [IntToStr(Codigo)]), mbInformation, MB_OK);
    end;
  end;

  { 2. Firewall: sacar bloqueos viejos y abrir solo lo necesario (redes privadas, solo la red de casa) }
  WizardForm.StatusLabel.Caption := CustomMessage('Firewall');
  Programa := ExpandConstant('{app}\{#Exe}');
  CorrerPowerShell(
    'Get-NetFirewallApplicationFilter | Where-Object { $_.Program -like ''*ControlCelular*'' } | Get-NetFirewallRule | Where-Object Action -eq ''Block'' | Remove-NetFirewallRule; ' +
    'Get-NetFirewallRule -DisplayName ''CONTROL CELULAR*'' -ErrorAction SilentlyContinue | Remove-NetFirewallRule; ' +
    'New-NetFirewallRule -DisplayName ''CONTROL CELULAR'' -Description ''Control de juegos desde el celular (solo red local privada)'' -Direction Inbound -Action Allow -Protocol TCP -LocalPort 8765,8443 -Profile Private -RemoteAddress LocalSubnet | Out-Null; ' +
    'New-NetFirewallRule -DisplayName ''CONTROL CELULAR (programa)'' -Description ''Control de juegos desde el celular (solo red local privada)'' -Direction Inbound -Action Allow -Program ''' + Programa + ''' -Profile Private -RemoteAddress LocalSubnet | Out-Null');

  { 3. Versiones viejas, solo si la casilla está marcada (nunca el instalador que se está usando) }
  if WizardIsTaskSelected('limpiar') then
  begin
    WizardForm.StatusLabel.Caption := CustomMessage('Limpiando');
    Exec('powershell.exe', '-NoProfile -ExecutionPolicy Bypass -File "' + ExpandConstant('{tmp}\limpiar_viejas.ps1') +
         '" -Actual "' + ExpandConstant('{srcexe}') + '"', '', SW_HIDE, ewWaitUntilTerminated, Codigo);
  end;

  { 4. Red privada, solo si la persona marcó la casilla }
  if WizardIsTaskSelected('privada') then
  begin
    WizardForm.StatusLabel.Caption := CustomMessage('Red');
    CorrerPowerShell('Get-NetConnectionProfile | Where-Object NetworkCategory -eq ''Public'' | Set-NetConnectionProfile -NetworkCategory Private');
  end;
end;

function NeedRestart(): Boolean;
begin
  Result := ReiniciarPorDriver;
end;
