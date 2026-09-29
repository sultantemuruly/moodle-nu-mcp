"""Dev CLI to exercise each tool live, e.g. `uv run python main.py contents 21862`."""

import argparse
import asyncio
from collections.abc import Awaitable, Callable
from typing import Any

from playwright.async_api import Browser, async_playwright

from moodle_mcp import auth
from moodle_mcp.client import MoodleClient
from moodle_mcp.tools.assignments import assignment_status
from moodle_mcp.tools.courses import course_contents, list_courses
from moodle_mcp.tools.deadlines import course_deadlines, upcoming_deadlines
from moodle_mcp.tools.grades import course_grades
from moodle_mcp.tools.materials import download_materials, list_materials
from moodle_mcp.tools.messages import conversations, notifications

COMMANDS: dict[str, Callable[..., Awaitable[Any]]] = {
    "courses": list_courses,
    "contents": course_contents,
    "deadlines": upcoming_deadlines,
    "course-deadlines": course_deadlines,
    "assignment": assignment_status,
    "grades": course_grades,
    "materials": list_materials,
    "download": download_materials,
    "conversations": conversations,
    "notifications": notifications,
}


async def run(browser: Browser, command: str, args: list[int]) -> None:
    async with auth.session(browser) as context:
        result = await COMMANDS[command](await MoodleClient.connect(context), *args)
        for item in result.items() if isinstance(result, dict) else result:
            print(item)


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=COMMANDS)
    parser.add_argument("args", type=int, nargs="*", help="course id / cmid / days")
    ns = parser.parse_args()
    async with async_playwright() as pw:
        browser = await pw.chromium.launch()
        try:
            await run(browser, ns.command, ns.args)
        except auth.SessionExpiredError as e:
            print(f"{e}; opening browser for login...")
            await auth.login(pw)
            await run(browser, ns.command, ns.args)


if __name__ == "__main__":
    asyncio.run(main())
