import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=['--headless=new', '--disable-blink-features=AutomationControlled']
        )
        ctx = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            locale="en-US",
            viewport={"width": 1280, "height": 900},
        )
        page = await ctx.new_page()
        await page.goto("https://www.naukri.com/software-engineer-jobs-in-bangalore", wait_until="domcontentloaded")
        await page.wait_for_timeout(3000)
        
        cards = await page.query_selector_all('article.jobTuple, .srp-jobtuple-wrapper, div.jobTuple, div[data-job-id]')
        print(f"Found {len(cards)} cards")
        print("Page title:", await page.title())
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
