"""All traffic to NU Moodle: AJAX calls via service.php, page fetches otherwise; see docs/data-access.md."""

import re
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

from playwright.async_api import APIRequestContext, APIResponse, BrowserContext

from moodle_mcp.auth import SessionExpiredError
from moodle_mcp.config import BASE_URL


class MoodleError(Exception):
    def __init__(self, errorcode: str, message: str) -> None:
        super().__init__(f"{errorcode}: {message}")
        self.errorcode = errorcode


def parse_cfg(html: str) -> tuple[str, int]:
    """Extract (sesskey, userId) from M.cfg in a logged-in page."""
    sesskey = re.search(r'"sesskey":"(\w+)"', html)
    userid = re.search(r'"userId":(\d+)', html)
    if not (sesskey and userid):
        raise SessionExpiredError("No sesskey/userId in page; not logged in")
    return sesskey.group(1), int(userid.group(1))


def absolute(path_or_url: str) -> str:
    return path_or_url if path_or_url.startswith("http") else f"{BASE_URL}{path_or_url}"


@dataclass
class MoodleClient:
    request: APIRequestContext
    sesskey: str = ""
    userid: int = 0

    @classmethod
    async def connect(cls, context: BrowserContext) -> "MoodleClient":
        client = cls(context.request)
        await client.refresh_cfg()
        return client

    async def refresh_cfg(self) -> None:
        self.sesskey, self.userid = parse_cfg(await self.fetch_page("/my/"))

    async def fetch_page(self, path_or_url: str) -> str:
        return await (await self._get(path_or_url)).text()

    async def download(self, url: str) -> bytes:
        return await (await self._get(url)).body()

    async def resolve_redirect(self, url: str) -> str:
        """Return where a Moodle redirect points without following it (e.g. mod/url)."""
        response = await self.request.get(absolute(url), max_redirects=0)
        return response.headers.get("location", absolute(url))

    async def _get(self, path_or_url: str) -> APIResponse:
        response = await self.request.get(absolute(path_or_url))
        if urlparse(response.url).path.startswith("/login/"):
            raise SessionExpiredError(f"Redirected to login fetching {path_or_url}")
        return response

    async def call(self, method: str, args: dict[str, Any] | None = None) -> Any:
        try:
            return await self._call(method, args or {})
        except MoodleError as e:
            # sesskey can rotate while the session lives on; refresh once.
            if e.errorcode != "invalidsesskey":
                raise
            await self.refresh_cfg()
            return await self._call(method, args or {})

    async def _call(self, method: str, args: dict[str, Any]) -> Any:
        response = await self.request.post(
            f"{BASE_URL}/lib/ajax/service.php?info={method}&sesskey={self.sesskey}",
            data=[{"index": 0, "methodname": method, "args": args}],
        )
        [result] = await response.json()
        if not result["error"]:
            return result["data"]
        code, message = result["exception"]["errorcode"], result["exception"]["message"]
        if code == "servicerequireslogin":
            raise SessionExpiredError(message)
        raise MoodleError(code, message)
