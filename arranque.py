"""Punto de entrada de Control Celular (el .exe y iniciar.bat arrancan por acá).

Envuelve todo el programa para que NUNCA se cierre sin explicar:
- Si falta el driver ViGEmBus (vgamepad lo busca apenas se carga, antes que nada), muestra el aviso, abre la página
  de descarga y espera un Enter.
- Cualquier otro error al arrancar se muestra, se guarda en error.txt (en la carpeta de datos) y espera un Enter.

Para las pruebas: CONTROL_SIMULAR_SIN_VIGEM=1 simula una PC sin ViGEmBus; CONTROL_SIN_NAVEGADOR=1 no abre páginas.
"""

import os
import sys
import traceback

DESCARGA_VIGEMBUS = "https://github.com/nefarius/ViGEmBus/releases"


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


def _falta_vigembus() -> None:
    print()
    print(_texto("  Falta el driver ViGEmBus: es lo que crea el control virtual (es gratis y oficial).",
                 "  The ViGEmBus driver is missing: it's what creates the virtual controller (free and official)."))
    print(_texto("  Te abro la página para descargarlo:", "  Opening its download page:"))
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
            _falta_vigembus()
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
