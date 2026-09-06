import time
from rich.console import Console
from .config import Settings
from .fetch import fetch_cost_data
from .analyze import analyze_simple, analyze_seasonal
from .alert import dispatch_alerts

console = Console()

def watch_loop(settings: Settings, mode: str = "simple"):
    console.print(f"[bold green]Starting watch daemon. Interval: {settings.watch_interval_minutes} minutes.[/bold green]")
    while True:
        try:
            console.print("[cyan]Fetching latest Azure cost data...[/cyan]")
            df = fetch_cost_data(settings.azure_subscription_id)
            
            if mode == "seasonal":
                df_analyzed = analyze_seasonal(df, settings.alert_threshold_k)
            else:
                df_analyzed = analyze_simple(df, settings.alert_threshold_k)
                
            dispatch_alerts(df_analyzed, settings)
            console.print("[green]Check complete. Sleeping...[/green]")
        except Exception as e:
            console.print(f"[red]Error during watch iteration: {e}[/red]")
            
        try:
            time.sleep(settings.watch_interval_minutes * 60)
        except KeyboardInterrupt:
            console.print("[yellow]Watch daemon stopped by user.[/yellow]")
            break
