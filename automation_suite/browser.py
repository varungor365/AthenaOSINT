import asyncio
from typing import Dict, Any

# Playwright is optional; guard imports
try:
    from playwright.async_api import async_playwright
except Exception:  # pragma: no cover
    async_playwright = None

class BrowserAutomation:
    def __init__(self):
        self._playwright = None
        self._browser = None

    async def _ensure(self):
        if async_playwright is None:
            raise RuntimeError("Playwright not available. Install and set up browsers.")
        if self._playwright is None:
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(headless=True)

    async def navigate(self, url: str, actions: Dict[str, Any] | None = None) -> Dict[str, Any]:
        await self._ensure()
        page = await self._browser.new_page()
        await page.goto(url)
        # Basic actions (future: clicks, fills, waits)
        content = await page.content()
        title = await page.title()
        await page.close()
        return {"title": title, "html": content}

    async def screenshot(self, url: str) -> bytes:
        await self._ensure()
        page = await self._browser.new_page()
        await page.goto(url)
        img = await page.screenshot(full_page=True)
        await page.close()
        return img

    async def close(self):
        try:
            if self._browser:
                await self._browser.close()
            if self._playwright:
                await self._playwright.stop()
        finally:
            self._browser = None
            self._playwright = None
