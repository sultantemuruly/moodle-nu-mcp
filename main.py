import asyncio

from playwright.async_api import async_playwright

from moodle_mcp import auth
from moodle_mcp.config import STATE_PATH


async def main() -> None:
    async with async_playwright() as pw:
        browser = await pw.chromium.launch()
        try:
            async with auth.session(browser):
                print(f"Saved session is valid ({STATE_PATH})")
                return
        except auth.SessionExpiredError as e:
            print(f"{e}; opening browser for login...")
        await auth.login(pw)
        async with auth.session(browser):
            print(f"Logged in; session saved to {STATE_PATH}")


if __name__ == "__main__":
    asyncio.run(main())
