"""Browser-session auth for NU Moodle; see docs/authentication.md for why it isn't token-based."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import urlparse

from playwright.async_api import Browser, BrowserContext, Playwright

from moodle_mcp.config import BASE_URL, STATE_PATH

LOGIN_TIMEOUT_MS = 5 * 60_000


class SessionExpiredError(Exception):
    """No usable saved session; the user must log in again."""


def is_logged_in_url(url: str) -> bool:
    # Login ends when Moodle lands anywhere outside its login/auth pages.
    parsed = urlparse(url)
    on_moodle = f"{parsed.scheme}://{parsed.netloc}" == BASE_URL
    return on_moodle and not parsed.path.startswith(("/login/", "/auth/"))


async def login(pw: Playwright, state_path: Path = STATE_PATH) -> None:
    """Open a visible browser for manual login, then save the session."""
    browser = await pw.chromium.launch(headless=False)
    context = await browser.new_context()
    page = await context.new_page()
    await page.goto(f"{BASE_URL}/login/index.php")
    await page.wait_for_url(is_logged_in_url, timeout=LOGIN_TIMEOUT_MS)
    state_path.parent.mkdir(parents=True, exist_ok=True)
    await context.storage_state(path=state_path)
    state_path.chmod(0o600)
    await browser.close()


async def is_valid(context: BrowserContext) -> bool:
    # Without a live session Moodle answers /my/ with a 303 to the login page.
    response = await context.request.get(f"{BASE_URL}/my/", max_redirects=0)
    return response.ok


@asynccontextmanager
async def session(
    browser: Browser, state_path: Path = STATE_PATH
) -> AsyncIterator[BrowserContext]:
    """Yield a browser context authenticated with the saved session."""
    if not state_path.exists():
        raise SessionExpiredError(f"No saved session at {state_path}")
    context = await browser.new_context(storage_state=state_path)
    try:
        if not await is_valid(context):
            raise SessionExpiredError("Saved Moodle session has expired")
        yield context
    finally:
        await context.close()
