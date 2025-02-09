from playwright.async_api import async_playwright
from app.crawler.interfaces import IBrowserManager


class PlaywrightManager(IBrowserManager):
    def __init__(self):
        self.browser = None
        self.context = None

    async def setup(self):
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=True)
        self.context = await self.browser.new_context()

    async def cleanup(self):
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()

    async def create_page(self):
        return await self.context.new_page()
