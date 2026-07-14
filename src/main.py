"""CLI utilitária do LocalVoice.

Comandos:
- ``check``     executa o preflight de capacidades (Ollama e voz do Piper);
- ``gen-cert``  gera um certificado autoassinado para servir via HTTPS;
- ``serve``     sobe o gateway (HTTPS quando há certificado; senão HTTP);
- ``info``      mostra como iniciar cada serviço.
"""

import argparse
from pathlib import Path

from src.core.capabilities import describe_report, resolve_capabilities
from src.core.config import get_settings

_RUN_WORKER = "uv run faststream run src.worker.app:app"
_RUN_UI = "uv run --group ui streamlit run src/ui/app.py"


def _cmd_check() -> int:
    settings = get_settings()
    report = resolve_capabilities(settings)
    print("Preflight de capacidades:")
    for line in describe_report(report):
        print(f"  - {line}")
    print(f"\nPronto para operar: {'sim' if report.ready else 'não'}")
    return 0 if report.ready else 1


def _cmd_gen_cert() -> int:
    from src.gateway.tls import generate_self_signed_cert

    settings = get_settings()
    cert = settings.ssl_certfile or Path("certs/localvoice.crt")
    key = settings.ssl_keyfile or Path("certs/localvoice.key")
    hosts = generate_self_signed_cert(cert, key)
    print(f"Certificado: {cert}")
    print(f"Chave:       {key}")
    print(f"Hosts:       {', '.join(hosts)}")
    print("\nSuba o gateway em HTTPS com:  uv run localvoice serve")
    print("No navegador, aceite o aviso de certificado autoassinado uma vez.")
    return 0


def _cmd_serve() -> int:
    import uvicorn

    settings = get_settings()
    netloc = f"{settings.gateway_host}:{settings.gateway_port}"
    options: dict[str, object] = {
        "host": settings.gateway_host,
        "port": settings.gateway_port,
    }
    tls = settings.tls_files()
    if tls is not None:
        cert, key = tls
        options["ssl_certfile"] = str(cert)
        options["ssl_keyfile"] = str(key)
        print(f"Servindo HTTPS em https://{netloc}")
    else:
        print(f"Servindo HTTP em http://{netloc}")
        print("Sem TLS — rode 'localvoice gen-cert' para habilitar HTTPS.")
    uvicorn.run("src.gateway.app:app", **options)
    return 0


def _cmd_info() -> int:
    print("LocalVoice — serviços:")
    print("  Gerar cert : uv run localvoice gen-cert")
    print("  Gateway    : uv run localvoice serve")
    print(f"  Worker     : {_RUN_WORKER}")
    print(f"  UI         : {_RUN_UI}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(prog="localvoice", description=__doc__)
    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("check", help="Verifica Ollama e a voz do Piper.")
    subparsers.add_parser("gen-cert", help="Gera certificado autoassinado (HTTPS).")
    subparsers.add_parser("serve", help="Sobe o gateway (HTTPS se houver cert).")
    subparsers.add_parser("info", help="Mostra os comandos de execução.")

    args = parser.parse_args()
    dispatch = {
        "check": _cmd_check,
        "gen-cert": _cmd_gen_cert,
        "serve": _cmd_serve,
    }
    return dispatch.get(args.command, _cmd_info)()


if __name__ == "__main__":
    raise SystemExit(main())
