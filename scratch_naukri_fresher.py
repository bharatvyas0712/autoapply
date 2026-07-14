import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--window-position=-3000,-3000'
            ]
        )
        ctx = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            locale="en-US",
            viewport={"width": 1280, "height": 900},
        )
        page = await ctx.new_page()
        # Test ?experience=0
        await page.goto("https://www.naukri.com/software-engineer-jobs-in-pune?experience=0", wait_until="domcontentloaded")
        await page.wait_for_timeout(3000)
        
        cards = await page.query_selector_all('article.jobTuple, .srp-jobtuple-wrapper, div.jobTuple, div[data-job-id]')
        print(f"Found {len(cards)} cards for pune with experience=0")
        
        for card in cards[:3]:
            title_el = (await card.query_selector('a.title') or await card.query_selector('.title'))
            title = await title_el.inner_text() if title_el else "Unknown Title"
            print("Title:", title.strip())
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
