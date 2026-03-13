import time
import threading

import requests
import uvicorn
from rich.console import Console
from rich.table import Table

console = Console()

API_URL = "http://127.0.0.1:8000"

MONITORED_ENDPOINTS = {
    "Root":        ("GET",  "/"),
    "Chat":        ("POST", "/chat/message"),
    "Restaurantes":("GET",  "/restaurants"),
    "Pedidos":     ("GET",  "/orders"),
}


def _check_endpoint(method: str, path: str) -> tuple[bool, int]:
    url = f"{API_URL}{path}"
    try:
        if method == "GET":
            r = requests.get(url, timeout=3)
        else:
            # POST no /chat/message precisa de body mínimo para não retornar 422
            r = requests.post(url, json={"message": "ping"}, timeout=3)
        return r.status_code < 500, r.status_code
    except requests.exceptions.ConnectionError:
        return False, 0


def monitor_api() -> None:
    while True:
        try:
            # Usa o endpoint raiz como health-check (era /status, que não existe)
            root_ok, _ = _check_endpoint("GET", "/")
            console.clear()

            if root_ok:
                console.rule("[bold green]API Em execução[/bold green]")
                table = Table(title="Status dos Endpoints")
                table.add_column("Endpoint",  justify="left",   style="cyan",    no_wrap=True)
                table.add_column("Método",    justify="center", style="yellow")
                table.add_column("Status",    justify="center", style="magenta")
                table.add_column("HTTP Code", justify="center")

                for name, (method, path) in MONITORED_ENDPOINTS.items():
                    ok, code = _check_endpoint(method, path)
                    status = "[bold green]Online[/bold green]" if ok else "[bold red]Offline[/bold red]"
                    table.add_row(name, method, status, str(code) if code else "—")

                console.print(table)
            else:
                console.print("[bold red]API não está respondendo.[/bold red]")

        except Exception as exc:  # noqa: BLE001
            console.print(f"[bold red]Erro no monitor: {exc}[/bold red]")

        time.sleep(5)


def start_server() -> None:
    # Corrigido: módulo era "app:app" mas o objeto FastAPI está em api.main:app
    uvicorn.run("api.main:app", host="127.0.0.1", port=8000, reload=True)


if __name__ == "__main__":
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    time.sleep(2)
    monitor_api()