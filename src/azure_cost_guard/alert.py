import requests
import smtplib
from email.mime.text import MIMEText
import pandas as pd
from rich.console import Console
from rich.table import Table
from .config import Settings

console = Console()

def send_slack_alert(webhook_url: str, message: str) -> bool:
    try:
        response = requests.post(webhook_url, json={"text": message}, timeout=10)
        return response.status_code == 200
    except Exception:
        return False

def send_email_alert(settings: Settings, subject: str, body: str) -> bool:
    try:
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = settings.smtp_from
        msg['To'] = settings.smtp_to

        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
            server.starttls()
            if settings.smtp_user and settings.smtp_password:
                server.login(settings.smtp_user, settings.smtp_password)
            server.send_message(msg)
        return True
    except Exception:
        return False

def dispatch_alerts(df: pd.DataFrame, settings: Settings):
    anomalies = df[df['is_anomaly']]
    if anomalies.empty:
        return

    messages = []
    for _, row in anomalies.iterrows():
        date_str = row['date'].strftime('%Y-%m-%d')
        msg = (
            f"*Anomaly Detected* ({row['severity']})\n"
            f"Date: {date_str}\n"
            f"Actual Cost: ${row['cost']:.2f}\n"
            f"Expected Cost: ${row['expected_cost']:.2f}\n"
            f"Deviation: {row['deviation']:.1f}%\n"
        )
        messages.append(msg)
    
    full_message = "\n---\n".join(messages)
    
    # Try Slack
    if settings.slack_webhook_url:
        success = send_slack_alert(settings.slack_webhook_url, full_message)
        if success:
            return
            
    # Fallback to Email
    if settings.smtp_host and settings.smtp_from and settings.smtp_to:
        send_email_alert(settings, "Azure Cost Anomaly Alert", full_message)


def generate_sparkline(data: list[float], anomalies: list[bool]) -> str:
    """Generates an ASCII sparkline with anomalies marked in red."""
    if not data:
        return ""
        
    chars = '.-~*+=#'
    min_val, max_val = min(data), max(data)
    range_val = max_val - min_val if max_val > min_val else 1
    
    sparkline = ""
    for val, is_anom in zip(data, anomalies):
        idx = int((val - min_val) / range_val * (len(chars) - 1))
        char = chars[idx]
        if is_anom:
            sparkline += f"[red]{char}[/red]"
        else:
            sparkline += f"[green]{char}[/green]"
            
    return sparkline

def display_terminal_output(df: pd.DataFrame):
    if df.empty:
        console.print("[yellow]No data available.[/yellow]")
        return
        
    # Print sparkline
    console.print("\n[bold]Cost Trend[/bold]:")
    spark = generate_sparkline(df['cost'].tolist(), df['is_anomaly'].tolist())
    console.print(spark)
    console.print()
    
    # Print Table
    table = Table(title="Daily Azure Costs")
    table.add_column("Date", style="cyan")
    table.add_column("Cost", justify="right")
    table.add_column("Expected", justify="right")
    table.add_column("Dev %", justify="right")
    table.add_column("Severity")
    
    for _, row in df.iterrows():
        date_str = row['date'].strftime('%Y-%m-%d')
        cost_str = f"${row['cost']:.2f}"
        exp_str = f"${row['expected_cost']:.2f}"
        dev_str = f"{row['deviation']:.1f}%"
        sev_str = row['severity']
        
        if row['is_anomaly']:
            style = "bold red"
            table.add_row(date_str, cost_str, exp_str, dev_str, sev_str, style=style)
        else:
            table.add_row(date_str, cost_str, exp_str, dev_str, sev_str)
            
    console.print(table)
