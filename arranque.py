"""Punto de entrada de Control Celular (el .exe y iniciar.bat arrancan por acá).

Envuelve todo el programa para que NUNCA se cierre sin explicar:
- Si falta el driver ViGEmBus (vgamepad lo busca apenas se carga, antes que nada), muestra el aviso, abre la página
  de descarga y espera un Enter.
- Cualquier otro error al arrancar se muestra, se guarda en error.txt (en la carpeta de datos) y espera un Enter.

El instalador OFICIAL de ViGEmBus viene incluido (terceros/, licencia BSD 3 en terceros/LICENCIA-ViGEmBus.txt):
si falta el driver, se ofrece instalarlo con un "sí". Antes de abrirlo se comprueba su huella SHA-256, así no se
puede reemplazar por otro archivo.

Para las pruebas: CONTROL_SIMULAR_SIN_VIGEM=1 simula una PC sin ViGEmBus; CONTROL_SIMULAR_INSTALADOR=1 hace de
cuenta que el instalador terminó bien (no abre nada); CONTROL_SIN_NAVEGADOR=1 no abre páginas.
"""

import hashlib
import os
import subprocess
import sys
import traceback
from pathlib import Path

DESCARGA_VIGEMBUS = "https://github.com/nefarius/ViGEmBus/releases"
INSTALADOR_VIGEMBUS = "ViGEmBus_1.22.0_x64_x86_arm64.exe"
SHA256_INSTALADOR = "89220a7865076b342892f98865f3499fb7c4cfd673159e89d352c360fd014c6a"
REINICIO_NECESARIO = 3010  # código de salida de los instaladores de Windows: "instalado, falta reiniciar"


def _texto(es: str, en: str) -> str:
    try:
        from idioma import T
        return T(es, en)
    except Exception:
        return es


def _esperar_enter() -> None:
    try:
        input(_texto("  Presioná Enter para cerrar...", "  Press Enter to close..."))
    except (EOFError, OSError, KeyboardInterrupt):
        pass


def _falta_vigembus(ya_explicado: bool = False) -> None:
    print()
    if not ya_explicado:
        print(_texto("  Falta el driver ViGEmBus: es lo que crea el control virtual (es gratis y oficial).",
                     "  The ViGEmBus driver is missing: it's what creates the virtual controller (free and official)."))
    print(_texto("  Para instalarlo a mano, te abro su página:", "  To install it manually, opening its page:"))
    print(f"    {DESCARGA_VIGEMBUS}")
    print(_texto("  Bajá ViGEmBus_..._x64_x86_arm64.exe, instalalo (si lo pide, reiniciá) y volvé a abrir Control Celular.",
                 "  Download ViGEmBus_..._x64_x86_arm64.exe, install it (restart if asked) and open Control Celular again."))
    print()
    if os.environ.get("CONTROL_SIN_NAVEGADOR") != "1":
        try:
            import webbrowser
            webbrowser.open(DESCARGA_VIGEMBUS)
        except Exception:
            pass


def _preguntar(texto: str) -> bool:
    try:
        return input(texto).strip().lower() in ("s", "si", "sí", "y", "yes")
    except (EOFError, OSError, KeyboardInterrupt):
        return False


def _instalador_incluido() -> Path | None:
    try:
        import rutas
        p = rutas.RECURSOS / "terceros" / INSTALADOR_VIGEMBUS
    except Exception:
        p = Path(__file__).resolve().parent / "terceros" / INSTALADOR_VIGEMBUS
    return p if p.is_file() else None


def _es_el_oficial(p: Path) -> bool:
    return hashlib.sha256(p.read_bytes()).hexdigest() == SHA256_INSTALADOR


def _correr_instalador(p: Path) -> int:
    """Abre el instalador oficial con permiso de administrador (Windows pregunta) y espera a que termine."""
    if os.environ.get("CONTROL_SIMULAR_INSTALADOR") == "1":
        return 0
    orden = (f"try {{ $p = Start-Process -FilePath '{p}' -Verb RunAs -Wait -PassThru -ErrorAction Stop; "
             f"exit $p.ExitCode }} catch {{ exit 1223 }}")  # 1223 = el usuario tocó «No» en el permiso
    return subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", orden]).returncode


def _reabrir() -> int:
    """Vuelve a abrir Control Celular en la misma ventana, ahora con el driver instalado."""
    if getattr(sys, "frozen", False):
        orden = [sys.executable]
    else:
        orden = [sys.executable, "-u", str(Path(__file__).resolve())]
    orden += [a for a in sys.argv[1:] if a != "--tras-instalar"] + ["--tras-instalar"]
    return subprocess.call(orden)


def _resolver_vigembus() -> int:
    """Falta ViGEmBus: ofrecer el instalador incluido; si no se puede, explicar cómo bajarlo."""
    if "--tras-instalar" in sys.argv:  # ya se instaló y Windows todavía no lo ve
        print()
        print(_texto("  ViGEmBus ya se instaló, pero Windows todavía no lo reconoce.",
                     "  ViGEmBus was installed, but Windows doesn't see it yet."))
        print(_texto("  Reiniciá la PC y volvé a abrir Control Celular.", "  Restart your PC and open Control Celular again."))
        print()
        return 1
    instalador = _instalador_incluido()
    if instalador is None or "--minimizado" in sys.argv:
        _falta_vigembus()
        return 1
    print()
    print(_texto("  Falta el driver ViGEmBus: es lo que crea el control virtual (gratis y oficial).",
                 "  The ViGEmBus driver is missing: it's what creates the virtual controller (free and official)."))
    print(_texto("  Viene incluido con Control Celular: es el instalador oficial, firmado por su autor (Nefarius).",
                 "  It comes included with Control Celular: the official installer, signed by its author (Nefarius)."))
    if not _preguntar(_texto("  ¿Lo instalo ahora? Windows te va a pedir permiso (S/N): ",
                             "  Install it now? Windows will ask for permission (Y/N): ")):
        _falta_vigembus(ya_explicado=True)
        return 1
    if not _es_el_oficial(instalador):
        print(_texto("  El instalador incluido no es el oficial (su huella no coincide): no lo abro por seguridad.",
                     "  The included installer isn't the official one (fingerprint mismatch): not opening it."))
        _falta_vigembus(ya_explicado=True)
        return 1
    print(_texto("  Abriendo el instalador: aceptá el permiso de Windows y tocá «Instalar» / «Siguiente»...",
                 "  Opening the installer: accept Windows' prompt and click Install / Next..."))
    codigo = _correr_instalador(instalador)
    if codigo == REINICIO_NECESARIO:
        print()
        print(_texto("  Listo, ViGEmBus quedó instalado. Windows pide reiniciar la PC: reiniciá y volvé a abrir Control Celular.",
                     "  Done, ViGEmBus is installed. Windows asks for a restart: restart and open Control Celular again."))
        print()
        return 1
    if codigo != 0:
        print()
        print(_texto("  No se instaló (¿se canceló o tocaste «No» en el permiso?).",
                     "  It wasn't installed (was it cancelled, or did you click “No”?)."))
        _falta_vigembus(ya_explicado=True)
        return 1
    print(_texto("  Listo, ViGEmBus quedó instalado. Abriendo Control Celular...",
                 "  Done, ViGEmBus is installed. Opening Control Celular..."))
    sys.exit(_reabrir())  # el que se abre de nuevo ya muestra sus propios mensajes: acá no hay más nada que esperar


def _error_inesperado(e: BaseException) -> None:
    detalle = "".join(traceback.format_exception(type(e), e, e.__traceback__))
    archivo = None
    try:
        import rutas
        archivo = rutas.DATOS / "error.txt"
        archivo.write_text(detalle, "utf-8")
    except Exception:
        pass
    print()
    print(_texto("  Control Celular no pudo arrancar por un error inesperado:",
                 "  Control Celular couldn't start because of an unexpected error:"))
    print()
    print(detalle)
    if archivo:
        print(_texto(f"  (Quedó guardado en {archivo}: si pedís ayuda, mandá ese archivo.)",
                     f"  (Saved to {archivo}: if you ask for help, send that file.)"))
    print()


def main() -> None:
    try:  # mensajes al instante; si la salida va a un archivo, en UTF-8 (para acentos y el QR)
        if sys.stdout.isatty():
            sys.stdout.reconfigure(line_buffering=True)
        else:
            sys.stdout.reconfigure(line_buffering=True, encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
    try:
        if os.environ.get("CONTROL_SIMULAR_SIN_VIGEM") == "1":
            raise RuntimeError("Error: VIGEM_ERROR_BUS_NOT_FOUND")
        import server  # al cargarse, vgamepad busca el driver ViGEmBus
    except SystemExit:
        raise
    except Exception as e:
        if "VIGEM_ERROR_BUS_NOT_FOUND" in str(e) or "ViGEm" in type(e).__name__:
            _resolver_vigembus()  # si se instala, vuelve a abrir Control Celular y termina ahí mismo
        else:
            _error_inesperado(e)
        _esperar_enter()
        sys.exit(1)
    try:
        server.correr()
    except SystemExit:
        raise
    except Exception as e:
        _error_inesperado(e)
        _esperar_enter()
        sys.exit(1)


if __name__ == "__main__":
    main()
