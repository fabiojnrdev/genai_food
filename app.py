import uvicorn
import time
import threading
import requests
from rich.console import Console
from rich.table import Table


console = Console()

API_URL = "http://127.0.0.1:8000"

def monitor_api():
    while True:
        try:
            response = requests.get(f"{API_URL}/status")
            if response.status_code == 200:
                console.clear()
                console.rule("[bold green]API Em execução[/bold green]")
                table = Table(title="Status da API")
                table.add_column("Endpoint", justify="left", style="cyan", no_wrap=True)
                table.add_column("Status", justify="center", style="magenta")
                table.add_column("Mensagem", justify = "left", style="green")

                endpoints = {
                    "Root": "/",
                    "Chat": "/chat/message",
                    "Restaurantes": "/restaurants",
                    "Pedidos": "/orders"
                }

                for name, endpoint in endpoints.items():
                    try:
                        r = requests.get(f"{API_URL}{endpoint}")
                        if r.status_code == 200:
                            table.add_row(name, "[bold green]Online[/bold green]", "Funcionando corretamente")
                        else:
                            table.add_row(name, "[bold red]Offline[/bold red]", f"Erro: {r.status_code}")
                    except Exception:
                        table.add_row(name, "[bold red]Offline[/bold red]", "Não foi possível conectar")

                console.print(table)
            else:
                console.print("[bold red]API não está respondendo corretamente.[/bold red]")
        except Exception:
            console.print("[bold red]Falha ao conectar com a API.[/bold red]")
        time.sleep(5)

def start_serv():
    uvicorn.run("app:app", host="127.0.0.1", port = 8000, reload=True)
if __name__ == "__main__":
    server_thread = threading.Thread(target=start_serv, daemon=True)
    server_thread.start()
    time.sleep(2)
    monitor_api()