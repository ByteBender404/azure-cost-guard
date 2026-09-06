import pytest
from unittest.mock import patch, MagicMock
from azure_cost_guard.alert import dispatch_alerts, send_slack_alert, send_email_alert
from azure_cost_guard.config import Settings
from azure_cost_guard.demo_data import generate_synthetic_data
from azure_cost_guard.analyze import analyze_simple

@patch('requests.post')
def test_send_slack_alert(mock_post):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_post.return_value = mock_response
    
    success = send_slack_alert("http://fake.webhook", "Test Message")
    assert success is True
    mock_post.assert_called_once()
    args, kwargs = mock_post.call_args
    assert kwargs['json']['text'] == "Test Message"

@patch('smtplib.SMTP')
def test_send_email_alert(mock_smtp):
    mock_server = MagicMock()
    mock_smtp.return_value.__enter__.return_value = mock_server
    
    settings = Settings(
        smtp_host="localhost",
        smtp_port=25,
        smtp_from="test@test.com",
        smtp_to="admin@test.com"
    )
    
    success = send_email_alert(settings, "Test Subject", "Test Body")
    assert success is True
    mock_server.send_message.assert_called_once()
    
@patch('azure_cost_guard.alert.send_slack_alert')
@patch('azure_cost_guard.alert.send_email_alert')
def test_dispatch_alerts(mock_email, mock_slack):
    df = generate_synthetic_data(days=30)
    df_analyzed = analyze_simple(df)
    
    settings = Settings(
        slack_webhook_url="http://fake.webhook",
        smtp_host="localhost"
    )
    
    mock_slack.return_value = True
    
    dispatch_alerts(df_analyzed, settings)
    
    # Since slack succeeds, email should not be called
    mock_slack.assert_called_once()
    mock_email.assert_not_called()
    
    # The message should contain severity strings
    args, _ = mock_slack.call_args
    message = args[1]
    assert "Severe" in message
    assert "Anomaly Detected" in message
