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
        await page.goto("https://www.naukri.com/job-listings-software-engineer-trainees-fresher-graduates-coddle-technologies-private-ltd-bengaluru-2-to-3-years-120226500637", wait_until="domcontentloaded")
        await page.wait_for_timeout(3000)
        
        # print out the apply section HTML
        try:
            btn = await page.query_selector('button:has-text("Applied")')
            if btn:
                print("Found button!")
                html = await btn.evaluate('el => el.outerHTML')
                print(html)
            else:
                div = await page.query_selector('div.apply-button-container')
                if div:
                    print("Found apply-button-container")
                    html = await div.evaluate('el => el.outerHTML')
                    print(html)
        except Exception as e:
            print("Error", e)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
