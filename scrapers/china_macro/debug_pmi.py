
import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        # November 2025 PMI URL (verified in browser history)
        url = "http://www.stats.gov.cn/english/PressRelease/202512/t20251202_1961963.html"
        await page.goto(url)
        content = await page.inner_text("body")
        print(content)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
