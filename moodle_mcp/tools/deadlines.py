import html
import time
from typing import Any

from moodle_mcp.client import MoodleClient
from moodle_mcp.models import Deadline, from_unix


def _deadline(event: dict[str, Any]) -> Deadline:
    return Deadline(
        name=html.unescape(
            event["name"]
        ),  # event names arrive entity-encoded ("E&#38;M")
        course=event["course"]["fullname"],
        module=event["modulename"],
        due=from_unix(event["timesort"]),
        overdue=event["overdue"],
        url=event["url"],
    )


async def upcoming_deadlines(
    m: MoodleClient, days: int = 30, overdue_days: int = 30
) -> list[Deadline]:
    """Actionable items (assignments, quizzes, ...) due within `days`, plus ones overdue by up to
    `overdue_days` that still await action, as on the dashboard Timeline."""
    now = int(time.time())
    data = await m.call(
        "core_calendar_get_action_events_by_timesort",
        {
            "timesortfrom": now - overdue_days * 86400,
            "timesortto": now + days * 86400,
            "limitnum": 50,
        },
    )
    return [_deadline(e) for e in data["events"]]


async def course_deadlines(m: MoodleClient, course_id: int) -> list[Deadline]:
    data = await m.call(
        "core_calendar_get_action_events_by_course", {"courseid": course_id}
    )
    return [_deadline(e) for e in data["events"]]
