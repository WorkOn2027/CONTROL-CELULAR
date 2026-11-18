"""Revisa (y si el usuario quiere, arregla) lo que hace falta en Windows para que el celular se conecte:

- Una regla de firewall que abra los puertos 8765 y 8443 solo en redes privadas y solo para la red local.
- Que la red de casa esté marcada como "Privada" (Windows marca como "Pública" cada red nueva).

Leer no necesita permisos. Para cambiar algo, Windows pide permiso de administrador (se abre su cartel).
"""

import subprocess
import tempfile
from pathlib import Path
from idioma import T

REGLA = "CONTROL CELULAR"
PUERTOS = "8765,8443"
_SIN_VENTANA = 0x08000000  # CREATE_NO_WINDOW


def _ps(comando: str) -> str:
    r = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", comando],
                       capture_output=True, text=True, creationflags=_SIN_VENTANA)
    return r.stdout.strip()


def _como_admin(script: str) -> bool:
    """Corre un script de PowerShell con permiso de administrador (Windows pregunta). True si salió bien."""
    with tempfile.TemporaryDirectory() as tmp:
        ps1, ok = Path(tmp) / "arreglo.ps1", Path(tmp) / "ok.txt"
        ps1.write_text(f"try {{ {script}; 'ok' | Out-File '{ok}' }} catch {{ $_ | Out-File '{ok}.error' }}",
                       encoding="utf-8-sig")
        _ps(f"Start-Process powershell -Verb RunAs -Wait -WindowStyle Hidden "
            f"-ArgumentList '-NoProfile -ExecutionPolicy Bypass -File \"{ps1}\"'")
        return ok.exists()


def regla_existe() -> bool:
    n = _ps(f"(Get-NetFirewallRule -DisplayName '{REGLA}' -ErrorAction SilentlyContinue | Measure-Object).Count")
    return n not in ("", "0")


def crear_regla() -> bool:
    return _como_admin(
        f"Get-NetFirewallRule -DisplayName '{REGLA}' -ErrorAction SilentlyContinue | Remove-NetFirewallRule; "
        f"New-NetFirewallRule -DisplayName '{REGLA}' -Description 'Control de juegos desde el celular (solo red "
        f"local privada)' -Direction Inbound -Action Allow -Protocol TCP -LocalPort {PUERTOS} -Profile Private "
        f"-RemoteAddress LocalSubnet -ErrorAction Stop | Out-Null")


def quitar_regla() -> bool:
    return _como_admin(f"Get-NetFirewallRule -DisplayName '{REGLA}' -ErrorAction Stop | "
                       f"Remove-NetFirewallRule -ErrorAction Stop")


def redes_publicas() -> list[str]:
    """Nombres de las redes conectadas que Windows tiene como 'Públicas'."""
    salida = _ps("Get-NetConnectionProfile | Where-Object NetworkCategory -eq 'Public' | "
                 "ForEach-Object { $_.Name + ' (' + $_.InterfaceAlias + ')' }")
    return [l for l in salida.splitlines() if l.strip()]


def hacer_privadas() -> bool:
    return _como_admin("Get-NetConnectionProfile | Where-Object NetworkCategory -eq 'Public' | "
                       "Set-NetConnectionProfile -NetworkCategory Private -ErrorAction Stop")


def revisar(preguntar: bool = True) -> None:
    """Se llama al arrancar. Si todo está bien, no dice nada. Con preguntar=False solo avisa (arranque oculto).

    En el programa instalado pregunta con carteles de Windows; con Python, en la consola (dialogos.py)."""
    from dialogos import avisar
    from dialogos import preguntar as pedir_permiso
    try:
        if not regla_existe():
            texto = T("  Para que el celular se pueda conectar hay que abrir el firewall de Windows\n"
                      "  (solo los puertos del control, solo en redes privadas y solo para tu red de casa).",
                      "  For your phone to connect, the Windows firewall needs to be opened\n"
                      "  (only the controller's ports, only on private networks and only for your home network).")
            if not preguntar:
                print(texto)
            elif pedir_permiso(texto, T("¿Lo abro ahora? Windows te va a pedir permiso.",
                                      "Open it now? Windows will ask for permission."),
                               T("  ¿Lo abro ahora? Windows te va a pedir permiso (S/N): ",
                                 "  Open it now? Windows will ask for permission (Y/N): ")):
                if crear_regla():
                    print(T("  Listo: firewall abierto.", "  Done: firewall opened."))
                else:
                    avisar(T("  No se pudo abrir el firewall (¿tocaste «No» en el permiso?). "
                             "Podés volver a abrir el programa.",
                             "  The firewall couldn't be opened (did you tap “No”?). You can open the program again."))
            print()
        publicas = redes_publicas()
        if publicas:
            texto = (T("  Tu red está marcada como PÚBLICA, así el celular no se puede conectar:",
                       "  Your network is marked as PUBLIC, so your phone can't connect:")
                     + "".join(f"\n    - {r}" for r in publicas))
            if not preguntar:
                print(texto)
            elif pedir_permiso(texto, T("¿Es la red de tu casa? ¿La marco como PRIVADA? Windows te va a pedir permiso.",
                                      "Is it your home network? Mark it as PRIVATE? Windows will ask for permission."),
                               T("  ¿Es la red de tu casa? ¿La marco como PRIVADA? (S/N): ",
                                 "  Is it your home network? Mark it as PRIVATE? (Y/N): ")):
                if hacer_privadas():
                    print(T("  Listo: red marcada como privada.", "  Done: network marked as private."))
                else:
                    avisar(T("  No se pudo cambiar. Hacelo en Configuración > Red e Internet > tu red > Privada.",
                             "  It couldn't be changed. Do it in Settings > Network & Internet > your network > "
                             "Private."))
            print()
    except Exception as e:  # nunca impedir que arranque el control por esto
        print(T("  (No pude revisar el firewall:", "  (I couldn't check the firewall:"), e, ")")
