import sys
import typer
from pathlib import Path
from rich.console import Console

from .config import load_config, generate_default_config
from .fetch import fetch_cost_data
from .analyze import analyze_simple, analyze_seasonal
from .alert import dispatch_alerts, display_terminal_output
from .watch import watch_loop
from .demo_data import generate_synthetic_data

app = typer.Typer(help="Azure Cost Guard - Detect billing anomalies in Azure cost data.")
console = Console()

@app.command()
def init(config_path: str = "config.yaml"):
    """Initialize a default config.yaml file."""
    p = Path(config_path)
    if p.exists():
        console.print(f"[yellow]Config file already exists at {config_path}[/yellow]")
    else:
        generate_default_config(p)
        console.print(f"[green]Generated default config at {config_path}[/green]")

@app.command()
def fetch(days: int = 30, config_path: str = "config.yaml"):
    """Fetch daily cost data from Azure Cost Management API."""
    settings = load_config(Path(config_path))
    console.print(f"[cyan]Fetching last {days} days of cost data for subscription {settings.azure_subscription_id}...[/cyan]")
    try:
        df = fetch_cost_data(settings.azure_subscription_id, days=days)
        console.print(f"[green]Successfully fetched {len(df)} days of data and cached to cost_data.csv.[/green]")
    except Exception as e:
        console.print(f"[red]Error fetching data: {e}[/red]")
        raise typer.Exit(code=1)

@app.command()
def analyze(
    mode: str = typer.Option("simple", help="Anomaly detection mode: 'simple' or 'seasonal'"),
    demo: bool = typer.Option(False, "--demo", help="Run with synthetic demo data"),
    config_path: str = "config.yaml"
):
    """Run anomaly detection on the cost history."""
    settings = load_config(Path(config_path))
    
    if demo:
        console.print("[yellow]Running in DEMO mode with synthetic data...[/yellow]")
        df = generate_synthetic_data(days=30)
    else:
        try:
            import pandas as pd
            df = pd.read_csv("cost_data.csv")
            df['date'] = pd.to_datetime(df['date'])
        except FileNotFoundError:
            console.print("[red]cost_data.csv not found. Run 'azure-cost-guard fetch' first.[/red]")
            raise typer.Exit(code=1)
            
    if mode == "seasonal":
        df_analyzed = analyze_seasonal(df, settings.alert_threshold_k)
    else:
        df_analyzed = analyze_simple(df, settings.alert_threshold_k)
        
    display_terminal_output(df_analyzed)
    
    severe_anomalies = df_analyzed[df_analyzed['severity'] == 'Severe']
    if not severe_anomalies.empty:
        console.print("[bold red]Severe anomalies detected![/bold red]")
        raise typer.Exit(code=1)

@app.command()
def alert(
    mode: str = typer.Option("simple", help="Anomaly detection mode: 'simple' or 'seasonal'"),
    demo: bool = typer.Option(False, "--demo", help="Run with synthetic demo data"),
    config_path: str = "config.yaml"
):
    """Analyze data and send alerts to Slack/SMTP if anomalies are found."""
    settings = load_config(Path(config_path))
    if demo:
        df = generate_synthetic_data(days=30)
    else:
        try:
            import pandas as pd
            df = pd.read_csv("cost_data.csv")
            df['date'] = pd.to_datetime(df['date'])
        except FileNotFoundError:
            console.print("[red]cost_data.csv not found. Run 'azure-cost-guard fetch' first.[/red]")
            raise typer.Exit(code=1)
            
    if mode == "seasonal":
        df_analyzed = analyze_seasonal(df, settings.alert_threshold_k)
    else:
        df_analyzed = analyze_simple(df, settings.alert_threshold_k)
        
    dispatch_alerts(df_analyzed, settings)
    console.print("[green]Alert dispatch complete.[/green]")

@app.command()
def watch(
    mode: str = typer.Option("simple", help="Anomaly detection mode: 'simple' or 'seasonal'"),
    config_path: str = "config.yaml"
):
    """Run daemon-style monitoring continuously."""
    settings = load_config(Path(config_path))
    watch_loop(settings, mode)

if __name__ == "__main__":
    app()
