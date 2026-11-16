"""Certificados, lectura de Steam, versión, páginas e iPhone."""

import ipaddress
import struct

from cryptography import x509

import certs
import hacer_iphone
import paginas
import steam
import version

ANDROID = "Mozilla/5.0 (Linux; Android 14; SM-A065M) AppleWebKit/537.36 Chrome/130 Mobile Safari/537.36"
IPHONE = "Mozilla/5.0 (iPhone; CPU iPhone OS 18_1 like Mac OS X) AppleWebKit/605.1.15 Version/18.1 Mobile/15E148"


# ---------- Certificados ----------

def test_certificados_restringidos_a_la_red_local():
    crt, _ = certs.preparar("192.168.0.50")
    ca = x509.load_pem_x509_certificate(certs.CA_CRT.read_bytes())
    srv = x509.load_pem_x509_certificate(crt.read_bytes())
    restr = ca.extensions.get_extension_for_class(x509.NameConstraints).value
    redes = {str(s.value) for s in restr.permitted_subtrees if isinstance(s, x509.IPAddress)}
    assert {"10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"} <= redes
    sans = srv.extensions.get_extension_for_class(x509.SubjectAlternativeName).value
    assert ipaddress.ip_address("192.168.0.50") in sans.get_values_for_type(x509.IPAddress)
    # El nombre del servidor NO puede ser la IP (chocaría con la restricción en Chrome/OpenSSL)
    assert srv.subject.rfc4514_string() != "CN=192.168.0.50"
    srv.verify_directly_issued_by(ca)


def test_si_cambia_la_ip_se_firma_otro_sin_cambiar_la_ca():
    certs.preparar("192.168.0.50")
    ca_antes = certs.CA_CRT.read_bytes()
    crt, _ = certs.preparar("10.0.0.7")
    assert certs.CA_CRT.read_bytes() == ca_antes  # el certificado instalado en el celular sigue sirviendo
    sans = x509.load_pem_x509_certificate(crt.read_bytes()).extensions.get_extension_for_class(
        x509.SubjectAlternativeName).value
    assert ipaddress.ip_address("10.0.0.7") in sans.get_values_for_type(x509.IPAddress)


# ---------- Steam ----------

def _appinfo_v29(appid: int, nombre: str, etiquetas: list[int]) -> bytes:
    """Arma un appinfo.vdf de mentira (formato v29) con un solo juego."""
    textos = ["appinfo", "common", "name", "type", "store_tags"] + [str(i) for i in range(len(etiquetas))]
    k = {t: i for i, t in enumerate(textos)}
    kv = b"\x00" + struct.pack("<I", k["appinfo"]) + b"\x00" + struct.pack("<I", k["common"])
    kv += b"\x01" + struct.pack("<I", k["name"]) + nombre.encode() + b"\0"
    kv += b"\x01" + struct.pack("<I", k["type"]) + b"Game\0"
    kv += b"\x00" + struct.pack("<I", k["store_tags"])
    for i, e in enumerate(etiquetas):
        kv += b"\x02" + struct.pack("<I", k[str(i)]) + struct.pack("<i", e)
    kv += b"\x08\x08\x08\x08"  # cierra store_tags, common, appinfo y el bloque del juego
    entrada = struct.pack("<II", appid, 60 + len(kv)) + b"\0" * 60 + kv
    cuerpo = entrada + struct.pack("<I", 0)
    tabla = struct.pack("<I", len(textos)) + b"".join(t.encode() + b"\0" for t in textos)
    cabecera_len = 16
    return struct.pack("<IIq", 0x07564429, 1, cabecera_len + len(cuerpo)) + cuerpo + tabla


def test_leer_appinfo_v29(tmp_path):
    (tmp_path / "appcache").mkdir()
    (tmp_path / "appcache" / "appinfo.vdf").write_bytes(_appinfo_v29(2486820, "Sonic Racing", [699, 492]))
    info = steam.leer_appinfo(tmp_path, {2486820})
    assert info[2486820]["name"] == "Sonic Racing"
    assert steam.tipo_de("Sonic Racing", info[2486820]) == "carreras"


def test_tipo_de_juego_por_etiquetas_y_nombre():
    assert steam.tipo_de("X", {"store_tags": {"0": 1663}}) == "disparos"
    assert steam.tipo_de("X", {"store_tags": {"0": 1774, "1": 701}}) == "deportes"  # deportes gana a "Shooter"
    assert steam.tipo_de("Tekken 8", {}) == "pelea"
    assert steam.tipo_de("Stardew Valley", {}) == "accion"


# ---------- Versión ----------

def test_comparar_versiones():
    assert version._numeros("v1.10.0") > version._numeros("1.9.9")
    assert version._numeros(version.VERSION) == version._numeros("v" + version.VERSION)


# ---------- Páginas ----------

def test_cada_celular_recibe_su_version():
    assert paginas.pagina_inicial(True, ANDROID) == "/index.html"
    assert paginas.pagina_inicial(True, IPHONE) == "/iphone.html"
    assert paginas.pagina_inicial(False, ANDROID) == "/configurar.html"
    assert paginas.pagina_inicial(False, IPHONE) == "/configurar-iphone.html"


def test_qr_lleva_la_direccion_y_el_codigo():
    html = paginas.pagina_qr("http://192.168.0.49:8765/?c=1234", "1234").decode()
    assert "<svg" in html and "1234" in html and "http://192.168.0.49:8765/" in html


# ---------- iPhone ----------

def test_la_version_de_iphone_esta_al_dia():
    """La versión de iPhone se genera desde la de Android: si alguien cambió una y no la otra, esto falla."""
    for archivo, esperado in hacer_iphone.archivos().items():
        assert archivo.read_text("utf-8") == esperado, (
            f"{archivo.name} está desactualizado: corré  python herramientas/hacer_iphone.py")


def test_la_version_de_iphone_tiene_lo_suyo_y_android_no():
    a = (hacer_iphone.WEB / "index.html").read_text("utf-8")
    i = (hacer_iphone.WEB / "iphone.html").read_text("utf-8")
    for propio in ["requestPermission", "agregarInicio", "apple-touch-icon", "gIOS("]:
        assert propio in i and propio not in a, propio
