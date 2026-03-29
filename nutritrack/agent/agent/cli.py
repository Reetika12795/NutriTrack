"""CLI entry point for the NutriTrack health agent."""

from __future__ import annotations

import argparse
import asyncio
import sys

from rich.console import Console

from agent.config import AgentConfig
from agent.core import HealthAgent

console = Console()


def main():
    parser = argparse.ArgumentParser(
        description="NutriTrack Platform Health Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic health check (no AI — just reachability + screenshots)
  nutritrack-agent check

  # Full AI-powered analysis (requires AGENT_ANTHROPIC_API_KEY)
  AGENT_ANTHROPIC_API_KEY=sk-ant-... nutritrack-agent check

  # Check with visible browser (non-headless)
  nutritrack-agent check --visible

  # Custom service URLs
  nutritrack-agent check --airflow-url http://myhost:8080
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Health check command
    check_parser = subparsers.add_parser("check", help="Run platform health check")
    check_parser.add_argument("--visible", action="store_true", help="Show browser window")
    check_parser.add_argument("--airflow-url", default=None, help="Airflow URL")
    check_parser.add_argument("--grafana-url", default=None, help="Grafana URL")
    check_parser.add_argument("--output-dir", default="screenshots", help="Output directory for screenshots/reports")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == "check":
        config = AgentConfig()
        if args.visible:
            config.headless = False
        if args.airflow_url:
            config.airflow_url = args.airflow_url
        if args.grafana_url:
            config.grafana_url = args.grafana_url
        if args.output_dir:
            config.screenshot_dir = args.output_dir

        agent = HealthAgent(config)
        report = asyncio.run(agent.run_health_check())

        # Exit code based on health
        if report.overall_status == "healthy":
            sys.exit(0)
        elif report.overall_status == "critical":
            sys.exit(2)
        else:
            sys.exit(1)


if __name__ == "__main__":
    main()
