"""Preguntas y avisos a la persona.

El programa instalado no tiene consola (es una app de ventanas): pregunta y avisa con carteles de Windows.
Con Python (iniciar.bat) o en las pruebas hay consola: pregunta S/N y avisa escribiendo, como siempre.
"""

import ctypes
import sys

SI = ("s", "si", "sí", "y", "yes")


def hay_consola() -> bool:
    return sys.__stdout__ is not None and sys.__stdin__ is not None


def interactivo() -> bool:
    """Lo está usando una persona: programa de ventanas, o consola de verdad (no pruebas con la salida a un archivo)."""
    if sys.__stdout__ is None:
        return True
    try:
        return sys.__stdout__.isatty()
    except (AttributeError, ValueError):
        return False


def _esperar_animacion() -> None:
    """Que el cartel no aparezca encima de la animación de arranque."""
    try:
        import animacion
        animacion.terminada.wait(5)
    except Exception:
        pass


def _cartel(texto: str, estilo: int) -> int:
    _esperar_animacion()
    texto = "\n".join(linea.strip() for linea in texto.strip().splitlines())  # sin la sangría de la consola
    MB_TOPMOST, MB_SETFOREGROUND = 0x40000, 0x10000
    try:
        return ctypes.windll.user32.MessageBoxW(None, texto, "Control Celular", estilo | MB_TOPMOST | MB_SETFOREGROUND)
    except Exception:
        return 0


def preguntar(texto: str, pregunta: str, pregunta_consola: str) -> bool:
    """`texto` explica y `pregunta` va abajo en el cartel. En la consola se escribe el texto y se pregunta con
    `pregunta_consola` (termina en «(S/N): »)."""
    if hay_consola():
        print(texto)
        try:
            return input(pregunta_consola).strip().lower() in SI
        except (EOFError, OSError, KeyboardInterrupt, RuntimeError):  # nadie para responder: no tocar nada
            return False
    MB_YESNO, MB_ICONQUESTION, IDYES = 0x4, 0x20, 6
    return _cartel(f"{texto.strip()}\n\n{pregunta}", MB_YESNO | MB_ICONQUESTION) == IDYES


def avisar(texto: str, error: bool = False) -> None:
    if hay_consola():
        print(texto)
        return
    MB_ICONERROR, MB_ICONINFORMATION = 0x10, 0x40
    _cartel(texto, MB_ICONERROR if error else MB_ICONINFORMATION)


def esperar_enter(texto: str) -> None:
    """En la consola, que no se cierre antes de leer el mensaje. Sin consola no hace falta (el cartel ya esperó)."""
    if hay_consola():
        try:
            input(texto)
        except (EOFError, OSError, KeyboardInterrupt, RuntimeError):
            pass
