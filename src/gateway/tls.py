"""Geração de certificado autoassinado para servir o gateway via HTTPS.

Uso em desenvolvimento/LAN: um certificado autoassinado faz o navegador tratar a
origem como contexto seguro (necessário para a Web Speech API e
``crypto.randomUUID``), após o usuário aceitar o aviso de segurança uma vez.
"""

import datetime
import ipaddress
import socket
from pathlib import Path

_CERT_VALIDITY_DAYS = 365
_RSA_KEY_SIZE = 2048


def _local_ipv4_addresses() -> list[str]:
    """Descobre endereços IPv4 locais para incluir no certificado."""
    addresses = {"127.0.0.1"}
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("8.8.8.8", 80))
            addresses.add(sock.getsockname()[0])
    except OSError:
        pass
    return sorted(addresses)


def generate_self_signed_cert(
    cert_path: Path,
    key_path: Path,
    *,
    extra_hosts: list[str] | None = None,
) -> list[str]:
    """Gera um par cert/chave autoassinado cobrindo localhost e os IPs locais.

    Requer o pacote ``cryptography`` (grupo de dependência ``tls``). Retorna a
    lista de hosts incluídos no certificado.
    """
    try:
        from cryptography import x509
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.x509.oid import NameOID
    except ImportError as error:
        raise RuntimeError(
            "O pacote 'cryptography' é necessário para gerar o certificado. "
            "Instale com: uv sync --group tls"
        ) from error

    dns_names = ["localhost"]
    ip_addresses = _local_ipv4_addresses()
    for host in extra_hosts or []:
        try:
            ipaddress.ip_address(host)
            if host not in ip_addresses:
                ip_addresses.append(host)
        except ValueError:
            if host not in dns_names:
                dns_names.append(host)

    key = rsa.generate_private_key(public_exponent=65537, key_size=_RSA_KEY_SIZE)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "LocalVoice")])
    san = [x509.DNSName(dns) for dns in dns_names]
    san += [x509.IPAddress(ipaddress.ip_address(ip)) for ip in ip_addresses]

    now = datetime.datetime.now(datetime.UTC)
    certificate = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - datetime.timedelta(minutes=1))
        .not_valid_after(now + datetime.timedelta(days=_CERT_VALIDITY_DAYS))
        .add_extension(x509.SubjectAlternativeName(san), critical=False)
        .sign(key, hashes.SHA256())
    )

    cert_path.parent.mkdir(parents=True, exist_ok=True)
    cert_path.write_bytes(certificate.public_bytes(serialization.Encoding.PEM))
    key_path.write_bytes(
        key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )
    return dns_names + ip_addresses
