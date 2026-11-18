"""Revisa (y si el usuario quiere, arregla) lo que hace falta en Windows para que el celular se conecte:
una regla de firewall que abra los puertos 8765 y 8443 SOLO para la red local (la de casa), esté la red marcada
como «Privada» o como «Pública» (Windows marca como «Pública» casi toda red nueva, y así fallaba en muchas casas).

Aunque la red sea pública, nadie de afuera de tu red local puede llegar, y para usar el control hace falta el código
de emparejamiento (que solo está en tu pantalla y tiene límite de intentos).

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
    """Hay alguna regla de Control Celular (sirva o no para redes públicas)."""
    n = _ps(f"(Get-NetFirewallRule -DisplayName '{REGLA}*' -ErrorAction SilentlyContinue | Measure-Object).Count")
    return n not in ("", "0")


def regla_sirve() -> bool:
    """La regla de los puertos está activa y vale también en redes «Públicas» (las de antes eran solo privadas)."""
    n = _ps(f"(Get-NetFirewallRule -DisplayName '{REGLA}' -ErrorAction SilentlyContinue | Where-Object {{ "
            f"$_.Enabled -eq 'True' -and $_.Action -eq 'Allow' -and "
            f"($_.Profile -eq 'Any' -or $_.Profile.ToString() -like '*Public*') }} | Measure-Object).Count")
    return n not in ("", "0")


def crear_regla() -> bool:
    """Crea (o reemplaza) la regla: entrada TCP 8765/8443, cualquier tipo de red, SOLO desde la red local."""
    return _como_admin(
        f"Get-NetFirewallRule -DisplayName '{REGLA}' -ErrorAction SilentlyContinue | Remove-NetFirewallRule; "
        f"New-NetFirewallRule -DisplayName '{REGLA}' -Description 'Control de juegos desde el celular (solo red "
        f"local)' -Direction Inbound -Action Allow -Protocol TCP -LocalPort {PUERTOS} -Profile Any "
        f"-RemoteAddress LocalSubnet -ErrorAction Stop | Out-Null")


def quitar_regla() -> bool:
    return _como_admin(f"Get-NetFirewallRule -DisplayName '{REGLA}*' -ErrorAction Stop | "
                       f"Remove-NetFirewallRule -ErrorAction Stop")


def revisar(preguntar: bool = True) -> None:
    """Se llama al arrancar. Si todo está bien, no dice nada. Con preguntar=False solo avisa (arranque oculto).

    En el programa instalado pregunta con carteles de Windows; con Python, en la consola (dialogos.py)."""
    from dialogos import avisar
    from dialogos import preguntar as pedir_permiso
    try:
        if regla_sirve():
            return
        if regla_existe():  # de una versión anterior: solo servía en redes privadas
            texto = T("  Hay que actualizar la regla del firewall de Control Celular: la de antes solo andaba si\n"
                      "  Windows tenía tu red como «Privada» (y casi siempre la marca como «Pública»).\n"
                      "  La nueva sigue abierta SOLO para tu red de casa.",
                      "  Control Celular's firewall rule needs an update: the old one only worked if Windows had\n"
                      "  your network as “Private” (and it usually marks it as “Public”).\n"
                      "  The new one is still open ONLY to your home network.")
        else:
            texto = T("  Para que el celular se pueda conectar hay que abrir el firewall de Windows\n"
                      "  (solo los puertos del control y solo para tu red de casa).",
                      "  For your phone to connect, the Windows firewall needs to be opened\n"
                      "  (only the controller's ports and only for your home network).")
        if not preguntar:
            print(texto)
        elif pedir_permiso(texto, T("¿Lo hago ahora? Windows te va a pedir permiso.",
                                    "Do it now? Windows will ask for permission."),
                           T("  ¿Lo hago ahora? Windows te va a pedir permiso (S/N): ",
                             "  Do it now? Windows will ask for permission (Y/N): ")):
            if crear_regla():
                print(T("  Listo: firewall abierto para tu red de casa.", "  Done: firewall opened for your home network."))
            else:
                avisar(T("  No se pudo abrir el firewall (¿tocaste «No» en el permiso?). "
                         "Podés volver a abrir el programa.",
                         "  The firewall couldn't be opened (did you tap “No”?). You can open the program again."))
        print()
    except Exception as e:  # nunca impedir que arranque el control por esto
        print(T("  (No pude revisar el firewall:", "  (I couldn't check the firewall:"), e, ")")
