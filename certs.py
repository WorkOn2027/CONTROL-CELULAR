"""Certificados para HTTPS en la red de casa.

Crea una autoridad (CA) propia que se instala una sola vez en el celular, y con ella firma el certificado del
servidor para la IP actual de la PC. Si la IP cambia, se vuelve a firmar solo (la CA del celular sigue sirviendo).

Seguridad: la CA está *restringida* (Name Constraints) a direcciones IP privadas. Aunque alguien robara su clave,
no serviría para hacerse pasar por ningún sitio de internet (google.com, bancos, etc.): Chrome lo rechazaría.
"""

import datetime as dt
import ipaddress
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID

import rutas

CARPETA = rutas.DATOS / "certs"
CA_KEY, CA_CRT = CARPETA / "ca.key", CARPETA / "ca.crt"
SRV_KEY, SRV_CRT = CARPETA / "server.key", CARPETA / "server.crt"

REDES_PRIVADAS = ["10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16", "127.0.0.0/8"]


def _guardar_clave(clave, ruta: Path) -> None:
    ruta.write_bytes(clave.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                                         serialization.NoEncryption()))


def _ahora():
    return dt.datetime.now(dt.timezone.utc)


def _crear_ca():
    clave = ec.generate_private_key(ec.SECP256R1())
    nombre = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "CONTROL CELULAR (solo red local)")])
    restricciones = x509.NameConstraints(
        # Solo IPs privadas. El único nombre DNS permitido no existe (.invalid), así que ningún dominio real pasa.
        permitted_subtrees=[x509.DNSName("control-celular.invalid")]
        + [x509.IPAddress(ipaddress.ip_network(r)) for r in REDES_PRIVADAS],
        excluded_subtrees=None,
    )
    cert = (
        x509.CertificateBuilder()
        .subject_name(nombre).issuer_name(nombre)
        .public_key(clave.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(_ahora() - dt.timedelta(days=1))
        .not_valid_after(_ahora() + dt.timedelta(days=3650))
        .add_extension(x509.BasicConstraints(ca=True, path_length=0), critical=True)
        .add_extension(x509.KeyUsage(digital_signature=True, key_cert_sign=True, crl_sign=True,
                                     content_commitment=False, key_encipherment=False, data_encipherment=False,
                                     key_agreement=False, encipher_only=False, decipher_only=False), critical=True)
        .add_extension(restricciones, critical=True)
        .add_extension(x509.SubjectKeyIdentifier.from_public_key(clave.public_key()), critical=False)
        .sign(clave, hashes.SHA256())
    )
    _guardar_clave(clave, CA_KEY)
    CA_CRT.write_bytes(cert.public_bytes(serialization.Encoding.PEM))


def _crear_servidor(ip: str):
    ca_clave = serialization.load_pem_private_key(CA_KEY.read_bytes(), None)
    ca_cert = x509.load_pem_x509_certificate(CA_CRT.read_bytes())
    clave = ec.generate_private_key(ec.SECP256R1())
    ips = sorted({ip, "127.0.0.1"})
    cert = (
        x509.CertificateBuilder()
        # El CN no puede ser la IP: OpenSSL/Chrome lo tomarían como nombre DNS y chocaría con la restricción.
        .subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "Control Celular servidor")]))
        .issuer_name(ca_cert.subject)
        .public_key(clave.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(_ahora() - dt.timedelta(days=1))
        .not_valid_after(_ahora() + dt.timedelta(days=397))
        .add_extension(x509.SubjectAlternativeName([x509.IPAddress(ipaddress.ip_address(i)) for i in ips]),
                       critical=False)
        .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
        .add_extension(x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH]), critical=False)
        .add_extension(x509.AuthorityKeyIdentifier.from_issuer_public_key(ca_clave.public_key()), critical=False)
        .sign(ca_clave, hashes.SHA256())
    )
    _guardar_clave(clave, SRV_KEY)
    SRV_CRT.write_bytes(cert.public_bytes(serialization.Encoding.PEM))


def _servidor_sirve(ip: str) -> bool:
    try:
        cert = x509.load_pem_x509_certificate(SRV_CRT.read_bytes())
        sans = cert.extensions.get_extension_for_class(x509.SubjectAlternativeName).value
        vence = cert.not_valid_after_utc
    except (OSError, ValueError, x509.ExtensionNotFound):
        return False
    return ipaddress.ip_address(ip) in sans.get_values_for_type(x509.IPAddress) and \
        vence - _ahora() > dt.timedelta(days=30)


def preparar(ip: str) -> tuple[Path, Path]:
    """Deja listos los certificados para esta IP y devuelve (certificado, clave) del servidor."""
    CARPETA.mkdir(exist_ok=True)
    if not (CA_KEY.exists() and CA_CRT.exists()):
        _crear_ca()
    if not _servidor_sirve(ip):
        _crear_servidor(ip)
    return SRV_CRT, SRV_KEY


def ca_der() -> bytes:
    """La CA en formato DER, que es el que Android instala sin problemas."""
    return x509.load_pem_x509_certificate(CA_CRT.read_bytes()).public_bytes(serialization.Encoding.DER)
