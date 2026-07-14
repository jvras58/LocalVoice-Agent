"""CLI utilitária do LocalVoice.

Comandos:
- ``check``  executa o preflight de capacidades (Ollama e voz do Piper);
- ``info``   mostra como iniciar cada serviço.
"""

import argparse

from src.core.capabilities import describe_report, resolve_capabilities
from src.core.config import get_settings

_RUN_GATEWAY = "uv run uvicorn src.gateway.app:app --host 0.0.0.0 --port 8000"
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


def _cmd_info() -> int:
    print("LocalVoice — serviços:")
    print(f"  Gateway : {_RUN_GATEWAY}")
    print(f"  Worker  : {_RUN_WORKER}")
    print(f"  UI      : {_RUN_UI}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(prog="localvoice", description=__doc__)
    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("check", help="Verifica Ollama e a voz do Piper.")
    subparsers.add_parser("info", help="Mostra os comandos de execução.")

    args = parser.parse_args()
    if args.command == "check":
        return _cmd_check()
    return _cmd_info()


if __name__ == "__main__":
    raise SystemExit(main())
