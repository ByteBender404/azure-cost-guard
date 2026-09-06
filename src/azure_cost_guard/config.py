import yaml
from pathlib import Path
from pydantic import BaseModel, Field

class Settings(BaseModel):
    azure_subscription_id: str = Field(default="", description="Azure Subscription ID")
    alert_threshold_k: float = Field(default=3.0, description="Standard deviations for simple anomaly detection")
    slack_webhook_url: str = Field(default="", description="Slack Webhook URL")
    smtp_host: str = Field(default="", description="SMTP Host")
    smtp_port: int = Field(default=587, description="SMTP Port")
    smtp_user: str = Field(default="", description="SMTP User")
    smtp_password: str = Field(default="", description="SMTP Password")
    smtp_from: str = Field(default="", description="SMTP From Email")
    smtp_to: str = Field(default="", description="SMTP To Email")
    watch_interval_minutes: int = Field(default=1440, description="Interval in minutes for watch daemon (default 24h)")

def load_config(config_path: Path = Path("config.yaml")) -> Settings:
    if config_path.exists():
        with open(config_path, "r") as f:
            data = yaml.safe_load(f) or {}
            return Settings(**data)
    return Settings()

def generate_default_config(config_path: Path = Path("config.yaml")):
    settings = Settings(
        azure_subscription_id="your-subscription-id",
        slack_webhook_url="https://hooks.slack.com/services/...",
        smtp_host="smtp.gmail.com",
        smtp_user="user@example.com",
        smtp_from="alerts@example.com",
        smtp_to="admin@example.com"
    )
    with open(config_path, "w") as f:
        yaml.safe_dump(settings.model_dump(), f, default_flow_style=False, sort_keys=False)
