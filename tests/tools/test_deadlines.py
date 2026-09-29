import asyncio
from datetime import UTC, datetime
from typing import Any

from moodle_mcp.models import Deadline
from moodle_mcp.tools.deadlines import upcoming_deadlines


def test_upcoming_deadlines_unescapes_names(moodle: Any) -> None:
    moodle.results["core_calendar_get_action_events_by_timesort"] = {
        "events": [
            {
                "name": "E&#38;M Quiz 1 is due",
                "course": {"fullname": "Business"},
                "modulename": "assign",
                "timesort": 0,
                "overdue": True,
                "url": "u",
            }
        ]
    }
    assert asyncio.run(upcoming_deadlines(moodle)) == [
        Deadline(
            "E&M Quiz 1 is due",
            "Business",
            "assign",
            datetime(1970, 1, 1, tzinfo=UTC),
            True,
            "u",
        )
    ]
