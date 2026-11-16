"""Idioma de la ventana del programa y del ícono: español si Windows está en español, si no inglés.

Uso: T("Texto en español", "English text").
"""

import ctypes


def _windows_en_espanol() -> bool:
    try:
        lang = ctypes.windll.kernel32.GetUserDefaultUILanguage()
        return (lang & 0x3FF) == 0x0A  # 0x0A = español (cualquier país)
    except Exception:
        return True


ESPANOL = _windows_en_espanol()


def T(es: str, en: str) -> str:
    return es if ESPANOL else en
