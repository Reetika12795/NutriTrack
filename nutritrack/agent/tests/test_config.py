"""Tests for agent configuration."""

from agent.config import AgentConfig


def test_default_config():
    config = AgentConfig()
    assert config.airflow_url == "http://localhost:8080"
    assert config.fastapi_url == "http://localhost:8000"
    assert config.grafana_url == "http://localhost:3000"
    assert config.headless is True
    assert config.timeout_ms == 10000


def test_config_from_env(monkeypatch):
    monkeypatch.setenv("AGENT_AIRFLOW_URL", "http://custom:9090")
    monkeypatch.setenv("AGENT_HEADLESS", "false")
    config = AgentConfig()
    assert config.airflow_url == "http://custom:9090"
    assert config.headless is False


def test_service_check_dataclass():
    from agent.core import ServiceCheck

    check = ServiceCheck(name="Test", url="http://localhost")
    assert check.status == "unknown"
    assert check.issues == []
    assert check.metrics == {}


def test_health_report_to_dict():
    from agent.core import HealthReport, ServiceCheck

    check = ServiceCheck(name="Airflow", url="http://localhost:8080", status="healthy", summary="OK")
    report = HealthReport(timestamp="2026-03-30T00:00:00Z", overall_status="healthy", services=[check])
    d = report.to_dict()
    assert d["overall_status"] == "healthy"
    assert len(d["services"]) == 1
    assert d["services"][0]["name"] == "Airflow"
