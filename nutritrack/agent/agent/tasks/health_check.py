"""Deep health check task — navigates each service and performs detailed analysis."""

from __future__ import annotations

import asyncio

from rich.console import Console

from agent.browser import BrowserController
from agent.config import AgentConfig
from agent.vision import VisionAnalyzer

console = Console()


async def check_airflow_dags(browser: BrowserController, vision: VisionAnalyzer | None, config: AgentConfig) -> dict:
    """Navigate to Airflow and check DAG statuses."""
    result = {"service": "Airflow DAGs", "checks": []}

    try:
        await browser.navigate(config.airflow_url)

        # Login
        await browser.fill('input[name="username"]', config.airflow_user)
        await browser.fill('input[name="password"]', config.airflow_password)
        await browser.click('input[type="submit"], button[type="submit"]')
        await asyncio.sleep(3)

        # Navigate to DAGs list
        await browser.navigate(f"{config.airflow_url}/dags")
        await asyncio.sleep(2)

        # Screenshot the DAG list
        path, b64 = await browser.screenshot_base64("airflow_dags_list")

        if vision:
            analysis = vision.analyze_screenshot(
                b64,
                """Analyze this Airflow DAGs page. For each visible DAG, report:
1. DAG name
2. Status (active/paused)
3. Last run status (success/failed/running)
4. Any errors or warnings

Respond as JSON: {"dags": [{"name": "...", "active": true, "last_run": "success", "issues": []}]}""",
            )
            result["analysis"] = analysis
            result["screenshot"] = path
        else:
            result["screenshot"] = path
            result["analysis"] = "No AI analysis (set AGENT_ANTHROPIC_API_KEY)"

    except Exception as e:
        result["error"] = str(e)

    return result


async def check_grafana_dashboards(
    browser: BrowserController, vision: VisionAnalyzer | None, config: AgentConfig
) -> dict:
    """Navigate to Grafana and check SLA dashboard."""
    result = {"service": "Grafana SLA", "checks": []}

    try:
        await browser.navigate(config.grafana_url)

        # Login
        await browser.fill('input[name="user"]', config.grafana_user)
        await browser.fill('input[name="password"]', config.grafana_password)
        await browser.click('button[type="submit"]')
        await asyncio.sleep(3)

        # Navigate to dashboards
        await browser.navigate(f"{config.grafana_url}/dashboards")
        await asyncio.sleep(2)

        path, b64 = await browser.screenshot_base64("grafana_dashboards")

        if vision:
            analysis = vision.analyze_screenshot(
                b64,
                """Analyze this Grafana dashboards page. Report:
1. What dashboards are visible?
2. Are there any alerts firing?
3. Any panels showing errors or "No data"?

Respond as JSON: {"dashboards": [...], "alerts_firing": 0, "issues": []}""",
            )
            result["analysis"] = analysis
            result["screenshot"] = path
        else:
            result["screenshot"] = path
            result["analysis"] = "No AI analysis (set AGENT_ANTHROPIC_API_KEY)"

    except Exception as e:
        result["error"] = str(e)

    return result


async def check_api_health(browser: BrowserController, config: AgentConfig) -> dict:
    """Check FastAPI health endpoint programmatically."""
    result = {"service": "FastAPI", "checks": []}

    try:
        probe = await browser.check_reachable(f"{config.fastapi_url}/api/v1/health")
        result["reachable"] = probe["reachable"]
        result["status_code"] = probe.get("status")

        if probe["reachable"]:
            # Check the OpenAPI spec loads
            spec_probe = await browser.check_reachable(f"{config.fastapi_url}/openapi.json")
            result["openapi_available"] = spec_probe["reachable"]

    except Exception as e:
        result["error"] = str(e)

    return result


async def run_deep_health_check(config: AgentConfig | None = None) -> dict:
    """Run a deep health check across all NutriTrack services."""
    config = config or AgentConfig()
    browser = BrowserController(config)
    vision = VisionAnalyzer(config) if config.anthropic_api_key else None

    results = {}
    await browser.start()
    try:
        console.print("[bold]Running deep health check...[/]\n")

        results["airflow"] = await check_airflow_dags(browser, vision, config)
        results["grafana"] = await check_grafana_dashboards(browser, vision, config)
        results["api"] = await check_api_health(browser, config)

    finally:
        await browser.stop()

    return results
