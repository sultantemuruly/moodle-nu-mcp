import asyncio
from typing import Any

import pytest

from moodle_mcp.auth import SessionExpiredError
from moodle_mcp.client import MoodleClient, MoodleError, parse_cfg

PAGE = '<script>M.cfg = {"sesskey":"fresh","userId":42};</script>'


def error(code: str) -> list[dict[str, Any]]:
    return [{"error": True, "exception": {"errorcode": code, "message": code}}]


class FakeResponse:
    def __init__(
        self, body: Any = None, url: str = "https://moodle.nu.edu.kz/my/"
    ) -> None:
        self.body, self.url = body, url

    async def json(self) -> Any:
        return self.body

    async def text(self) -> str:
        return PAGE


class FakeRequest:
    """Replays queued service.php bodies; records the sesskey each call used."""

    def __init__(self, *bodies: Any) -> None:
        self.bodies, self.sesskeys = list(bodies), []

    async def post(self, url: str, data: Any) -> FakeResponse:
        self.sesskeys.append(url.rsplit("sesskey=", 1)[1])
        return FakeResponse(self.bodies.pop(0))

    async def get(self, url: str) -> FakeResponse:
        return FakeResponse()


def call(request: FakeRequest) -> Any:
    client = MoodleClient(request, sesskey="stale", userid=42)  # type: ignore[arg-type]
    return asyncio.run(client.call("some_method"))


def test_parse_cfg() -> None:
    assert parse_cfg(PAGE) == ("fresh", 42)


def test_parse_cfg_logged_out_raises() -> None:
    with pytest.raises(SessionExpiredError):
        parse_cfg("<html>login</html>")


def test_call_returns_data() -> None:
    assert call(FakeRequest([{"error": False, "data": {"x": 1}}])) == {"x": 1}


def test_call_refreshes_stale_sesskey_once() -> None:
    request = FakeRequest(error("invalidsesskey"), [{"error": False, "data": 7}])
    assert call(request) == 7
    assert request.sesskeys == ["stale", "fresh"]


def test_call_session_expired() -> None:
    with pytest.raises(SessionExpiredError):
        call(FakeRequest(error("servicerequireslogin")))


def test_call_unavailable_method() -> None:
    with pytest.raises(MoodleError, match="servicenotavailable"):
        call(FakeRequest(error("servicenotavailable")))
