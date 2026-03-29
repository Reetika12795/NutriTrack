"""Playwright browser controller for UI navigation."""

from __future__ import annotations

import base64
from pathlib import Path

from playwright.async_api import Browser, BrowserContext, Page, async_playwright

from agent.config import AgentConfig


class BrowserController:
    """Controls a headless browser for navigating NutriTrack UIs."""

    def __init__(self, config: AgentConfig):
        self.config = config
        self._playwright = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None
        self._page: Page | None = None
        self._screenshot_dir = Path(config.screenshot_dir)
        self._screenshot_dir.mkdir(parents=True, exist_ok=True)

    async def start(self) -> None:
        """Launch the browser."""
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(headless=self.config.headless)
        self._context = await self._browser.new_context(
            viewport={"width": 1920, "height": 1080},
            ignore_https_errors=True,
        )
        self._page = await self._context.new_page()
        self._page.set_default_timeout(self.config.timeout_ms)

    async def stop(self) -> None:
        """Close the browser."""
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()

    @property
    def page(self) -> Page:
        if not self._page:
            raise RuntimeError("Browser not started. Call start() first.")
        return self._page

    async def navigate(self, url: str) -> str:
        """Navigate to a URL and return the page title."""
        response = await self.page.goto(url, wait_until="networkidle", timeout=self.config.timeout_ms)
        status = response.status if response else "unknown"
        title = await self.page.title()
        return f"Navigated to {url} (status={status}, title={title})"

    async def screenshot(self, name: str) -> tuple[str, bytes]:
        """Take a screenshot and return (file_path, raw_bytes)."""
        path = self._screenshot_dir / f"{name}.png"
        raw = await self.page.screenshot(full_page=False)
        path.write_bytes(raw)
        return str(path), raw

    async def screenshot_base64(self, name: str) -> tuple[str, str]:
        """Take a screenshot and return (file_path, base64_encoded)."""
        path, raw = await self.screenshot(name)
        return path, base64.standard_b64encode(raw).decode("utf-8")

    async def click(self, selector: str) -> str:
        """Click an element by CSS selector."""
        await self.page.click(selector, timeout=self.config.timeout_ms)
        return f"Clicked: {selector}"

    async def fill(self, selector: str, value: str) -> str:
        """Fill a text input."""
        await self.page.fill(selector, value, timeout=self.config.timeout_ms)
        return f"Filled {selector} with value"

    async def wait_for(self, selector: str) -> str:
        """Wait for an element to appear."""
        await self.page.wait_for_selector(selector, timeout=self.config.timeout_ms)
        return f"Element found: {selector}"

    async def get_text(self, selector: str) -> str:
        """Get text content of an element."""
        element = await self.page.query_selector(selector)
        if element:
            return await element.text_content() or ""
        return ""

    async def check_reachable(self, url: str) -> dict:
        """Check if a URL is reachable without navigating the main page."""
        try:
            response = await self.page.request.get(url, timeout=self.config.timeout_ms)
            return {"url": url, "reachable": True, "status": response.status}
        except Exception as e:
            return {"url": url, "reachable": False, "error": str(e)}
