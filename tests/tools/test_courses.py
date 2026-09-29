import asyncio
import json
from typing import Any

from moodle_mcp.models import Activity, Section
from moodle_mcp.tools.courses import course_contents

URL = "https://moodle.nu.edu.kz/mod"

STATE = {
    "section": [
        {"number": 0, "title": "General", "cmlist": ["1", "2", "3"]},
        {"number": 1, "title": "Week 1", "cmlist": []},
    ],
    "cm": [
        {
            "id": "1",
            "module": "resource",
            "name": "Syllabus",
            "url": f"{URL}/resource/view.php?id=1",
            "uservisible": True,
        },
        {"id": "2", "module": "label", "name": "Welcome", "uservisible": True},
        {
            "id": "3",
            "module": "quiz",
            "name": "Hidden",
            "url": f"{URL}/quiz/view.php?id=3",
            "uservisible": False,
        },
    ],
}


def test_course_contents_maps_state_and_hides_invisible(moodle: Any) -> None:
    moodle.results["core_courseformat_get_state"] = json.dumps(STATE)
    assert asyncio.run(course_contents(moodle, 5)) == [
        Section(
            0,
            "General",
            [
                Activity(1, "resource", "Syllabus", f"{URL}/resource/view.php?id=1"),
                Activity(2, "label", "Welcome", ""),
            ],
        ),
        Section(1, "Week 1", []),
    ]
