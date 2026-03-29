"""Core agent loop: observe → think → act → report."""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone

from rich.console import Console
from rich.table import Table

from agent.browser import BrowserController
from agent.config import AgentConfig
from agent.vision import VisionAnalyzer

console = Console()


@dataclass
class ServiceCheck:
    """Result of checking a single service."""

    name: str
    url: str
    reachable: bool = False
    status: str = "unknown"
    summary: str = ""
    issues: list[str] = field(default_factory=list)
    metrics: dict = field(default_factory=dict)
    screenshot_path: str = ""
    checked_at: str = ""


@dataclass
class HealthReport:
    """Full platform health report."""

    timestamp: str
    overall_status: str
    services: list[ServiceCheck]
    total_issues: int = 0

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "overall_status": self.overall_status,
            "total_issues": self.total_issues,
            "services": [
                {
                    "name": s.name,
                    "url": s.url,
                    "reachable": s.reachable,
                    "status": s.status,
                    "summary": s.summary,
                    "issues": s.issues,
                    "metrics": s.metrics,
                    "screenshot": s.screenshot_path,
                    "checked_at": s.checked_at,
                }
                for s in self.services
            ],
        }


class HealthAgent:
    """AI-powered platform health monitoring agent."""

    SERVICES = [
        ("Airflow", "airflow_url", "/api/v1/health", "admin", "airflow"),
        ("FastAPI", "fastapi_url", "/docs", None, None),
        ("Grafana", "grafana_url", "/api/health", "admin", "grafana"),
        ("Streamlit", "streamlit_url", "", None, None),
        ("Superset", "superset_url", "/health", "admin", "superset"),
        ("MinIO", "minio_url", "/login", "admin", "minio"),
        ("MailHog", "mailhog_url", "", None, None),
    ]

    def __init__(self, config: AgentConfig | None = None):
        self.config = config or AgentConfig()
        self.browser = BrowserController(self.config)
        self.vision = VisionAnalyzer(self.config) if self.config.anthropic_api_key else None

    async def run_health_check(self) -> HealthReport:
        """Run a full platform health check across all services."""
        console.print("\n[bold green]NutriTrack Health Agent[/] starting...\n")
        checks: list[ServiceCheck] = []

        await self.browser.start()
        try:
            for name, url_attr, health_path, user_attr, cred_type in self.SERVICES:
                base_url = getattr(self.config, url_attr)
                check = await self._check_service(name, base_url, health_path, user_attr, cred_type)
                checks.append(check)
                self._print_check(check)
        finally:
            await self.browser.stop()

        # Determine overall status
        statuses = [c.status for c in checks]
        if all(s == "healthy" for s in statuses):
            overall = "healthy"
        elif any(s == "down" for s in statuses):
            overall = "critical"
        elif any(s == "degraded" for s in statuses):
            overall = "degraded"
        else:
            overall = "unknown"

        total_issues = sum(len(c.issues) for c in checks)

        report = HealthReport(
            timestamp=datetime.now(timezone.utc).isoformat(),
            overall_status=overall,
            services=checks,
            total_issues=total_issues,
        )

        self._print_summary(report)
        self._save_report(report)
        return report

    async def _check_service(
        self,
        name: str,
        base_url: str,
        health_path: str,
        user_attr: str | None,
        cred_type: str | None,
    ) -> ServiceCheck:
        """Check a single service: reachability → navigate → screenshot → analyze."""
        check = ServiceCheck(
            name=name,
            url=base_url,
            checked_at=datetime.now(timezone.utc).isoformat(),
        )

        # Step 1: Check reachability
        console.print(f"  [dim]Checking {name} at {base_url}...[/]")
        probe = await self.browser.check_reachable(base_url + health_path)
        check.reachable = probe["reachable"]

        if not check.reachable:
            check.status = "down"
            check.summary = f"{name} is not reachable at {base_url}"
            check.issues.append(f"Connection failed: {probe.get('error', 'unknown')}")
            return check

        # Step 2: Navigate to the service UI
        try:
            await self.browser.navigate(base_url)

            # Handle login if needed
            if user_attr and cred_type:
                await self._try_login(name, cred_type)

            await asyncio.sleep(2)  # Let the page fully render
        except Exception as e:
            check.status = "degraded"
            check.summary = f"Reachable but failed to load UI: {e}"
            check.issues.append(str(e))
            return check

        # Step 3: Screenshot
        try:
            screenshot_name = f"health_{name.lower()}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
            path, b64 = await self.browser.screenshot_base64(screenshot_name)
            check.screenshot_path = path
        except Exception as e:
            check.issues.append(f"Screenshot failed: {e}")
            check.status = "unknown"
            check.summary = "Could not capture screenshot"
            return check

        # Step 4: Analyze with Claude (if API key available)
        if self.vision:
            try:
                analysis = self.vision.analyze_health(b64, name)
                check.status = analysis.get("status", "unknown")
                check.summary = analysis.get("summary", "")
                check.issues = analysis.get("issues", [])
                check.metrics = analysis.get("metrics", {})
            except Exception as e:
                check.status = "unknown"
                check.summary = f"Vision analysis failed: {e}"
                check.issues.append(str(e))
        else:
            # No API key — basic status from reachability
            check.status = "healthy" if check.reachable else "down"
            check.summary = f"{name} UI loaded successfully (no AI analysis — set AGENT_ANTHROPIC_API_KEY)"

        return check

    async def _try_login(self, service: str, cred_type: str) -> None:
        """Attempt login for services that require authentication."""
        page = self.browser.page
        try:
            if cred_type == "airflow":
                await page.fill('input[name="username"]', self.config.airflow_user)
                await page.fill('input[name="password"]', self.config.airflow_password)
                await page.click('input[type="submit"], button[type="submit"]')
                await page.wait_for_load_state("networkidle")
            elif cred_type == "grafana":
                await page.fill('input[name="user"]', self.config.grafana_user)
                await page.fill('input[name="password"]', self.config.grafana_password)
                await page.click('button[type="submit"]')
                await page.wait_for_load_state("networkidle")
            elif cred_type == "superset":
                await page.fill('#username', self.config.superset_user)
                await page.fill('#password', self.config.superset_password)
                await page.click('input[type="submit"], button[type="submit"]')
                await page.wait_for_load_state("networkidle")
            elif cred_type == "minio":
                await page.fill('#accessKey', self.config.minio_user)
                await page.fill('#secretKey', self.config.minio_password)
                await page.click('button[type="submit"]')
                await page.wait_for_load_state("networkidle")
        except Exception:
            pass  # Login may not be required or selectors may differ

    def _print_check(self, check: ServiceCheck) -> None:
        """Print a single service check result."""
        icon = {"healthy": "[green]✓[/]", "degraded": "[yellow]![/]", "down": "[red]✗[/]"}.get(
            check.status, "[dim]?[/]"
        )
        console.print(f"  {icon} [bold]{check.name}[/] — {check.summary}")
        for issue in check.issues:
            console.print(f"      [red]↳ {issue}[/]")

    def _print_summary(self, report: HealthReport) -> None:
        """Print the full health report summary."""
        console.print()
        table = Table(title="NutriTrack Platform Health Report", show_header=True)
        table.add_column("Service", style="bold")
        table.add_column("URL")
        table.add_column("Status")
        table.add_column("Issues")
        table.add_column("Summary")

        for svc in report.services:
            status_style = {"healthy": "green", "degraded": "yellow", "down": "red"}.get(svc.status, "dim")
            table.add_row(
                svc.name,
                svc.url,
                f"[{status_style}]{svc.status}[/]",
                str(len(svc.issues)),
                svc.summary[:60],
            )

        console.print(table)

        overall_style = {"healthy": "green", "critical": "red", "degraded": "yellow"}.get(
            report.overall_status, "dim"
        )
        console.print(f"\n[bold]Overall: [{overall_style}]{report.overall_status.upper()}[/][/]")
        console.print(f"[dim]Total issues: {report.total_issues} | Timestamp: {report.timestamp}[/]\n")

    def _save_report(self, report: HealthReport) -> None:
        """Save the report as JSON."""
        from pathlib import Path

        report_dir = Path(self.config.screenshot_dir)
        report_dir.mkdir(parents=True, exist_ok=True)
        report_path = report_dir / f"health_report_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
        report_path.write_text(json.dumps(report.to_dict(), indent=2))
        console.print(f"[dim]Report saved to {report_path}[/]")
