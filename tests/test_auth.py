import asyncio
from pathlib import Path
from typing import Any

import pytest

from moodle_mcp import auth


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("https://moodle.nu.edu.kz/my/", True),
        ("https://moodle.nu.edu.kz/course/view.php?id=1", True),
        ("https://moodle.nu.edu.kz/login/index.php", False),
        ("https://moodle.nu.edu.kz/auth/oauth2/login.php", False),
        ("https://login.microsoftonline.com/common/oauth2", False),
    ],
)
def test_is_logged_in_url(url: str, expected: bool) -> None:
    assert auth.is_logged_in_url(url) is expected


def test_session_without_saved_state_raises(tmp_path: Path) -> None:
    async def open_session() -> None:
        browser: Any = None  # never touched: the missing file is detected first
        async with auth.session(browser, tmp_path / "missing.json"):
            pass

    with pytest.raises(auth.SessionExpiredError):
        asyncio.run(open_session())
