"""Testes da geração de certificado TLS (requer cryptography e datetime.UTC)."""

import datetime
import ssl
from pathlib import Path

import pytest

pytest.importorskip("cryptography")

if not hasattr(datetime, "UTC"):
    pytest.skip(
        "generate_self_signed_cert usa datetime.UTC (Python 3.11+)",
        allow_module_level=True,
    )

from src.gateway.tls import generate_self_signed_cert


def test_generate_self_signed_cert_creates_loadable_pair(tmp_path: Path) -> None:
    cert = tmp_path / "localvoice.crt"
    key = tmp_path / "localvoice.key"
    hosts = generate_self_signed_cert(cert, key, extra_hosts=["192.168.1.10"])

    assert "localhost" in hosts
    assert "192.168.1.10" in hosts
    assert cert.read_bytes().startswith(b"-----BEGIN CERTIFICATE-----")

    # Exatamente como o uvicorn carrega o par para servir HTTPS.
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain(certfile=str(cert), keyfile=str(key))
