import pytest
from pathlib import Path
from azure_cost_guard.config import Settings, load_config, generate_default_config

def test_generate_and_load_config(tmp_path):
    config_file = tmp_path / "config.yaml"
    generate_default_config(config_file)
    
    assert config_file.exists()
    
    settings = load_config(config_file)
    assert settings.azure_subscription_id == "your-subscription-id"
    assert settings.alert_threshold_k == 3.0
    assert settings.slack_webhook_url == "https://hooks.slack.com/services/..."
    assert settings.smtp_host == "smtp.gmail.com"
    assert settings.smtp_user == "user@example.com"
    
def test_load_non_existent_config(tmp_path):
    config_file = tmp_path / "does_not_exist.yaml"
    settings = load_config(config_file)
    # Should load default Settings
    assert settings.azure_subscription_id == ""
    assert settings.alert_threshold_k == 3.0
