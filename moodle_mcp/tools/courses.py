import json

from moodle_mcp.client import MoodleClient
from moodle_mcp.models import Activity, Course, Section


async def list_courses(
    m: MoodleClient, classification: str = "inprogress"
) -> list[Course]:
    """Enrolled courses; classification: inprogress | future | past | all | favourites | hidden."""
    data = await m.call(
        "core_course_get_enrolled_courses_by_timeline_classification",
        {"classification": classification, "limit": 0, "offset": 0, "sort": "fullname"},
    )
    return [
        Course(c["id"], c["fullname"], c["shortname"], c["viewurl"])
        for c in data["courses"]
    ]


async def course_contents(m: MoodleClient, course_id: int) -> list[Section]:
    """Sections with their visible activities, in course order."""
    # get_state returns a JSON string; ids are strings; `module` is the plugin key, `modname` its label.
    state = json.loads(
        await m.call("core_courseformat_get_state", {"courseid": course_id})
    )
    cms = {cm["id"]: cm for cm in state["cm"] if cm["uservisible"]}
    return [
        Section(
            number=section["number"],
            title=section["title"],
            activities=[
                Activity(int(cm["id"]), cm["module"], cm["name"], cm.get("url", ""))
                for cmid in section["cmlist"]
                if (cm := cms.get(cmid))
            ],
        )
        for section in state["section"]
    ]
