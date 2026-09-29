from typing import Any

import pytest


class FakeMoodle:
    """Stands in for MoodleClient: canned service.php results, pages, redirects and files."""

    userid = 7

    def __init__(self) -> None:
        self.results: dict[str, Any] = {}
        self.pages: dict[str, str] = {}
        self.redirects: dict[str, str] = {}
        self.files: dict[str, bytes] = {}
        self.downloaded: list[str] = []

    async def call(self, method: str, args: dict[str, Any] | None = None) -> Any:
        return self.results[method]

    async def fetch_page(self, url: str) -> str:
        return self.pages[url]

    async def resolve_redirect(self, url: str) -> str:
        return self.redirects[url]

    async def download(self, url: str) -> bytes:
        self.downloaded.append(url)
        return self.files[url]


@pytest.fixture
def moodle() -> Any:
    return FakeMoodle()
