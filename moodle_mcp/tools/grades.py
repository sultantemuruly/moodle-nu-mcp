from moodle_mcp.client import MoodleClient
from moodle_mcp.models import GradeItem
from moodle_mcp.parsers import parse_grade_items


async def course_grades(m: MoodleClient, course_id: int) -> list[GradeItem]:
    return parse_grade_items(
        await m.fetch_page(f"/grade/report/user/index.php?id={course_id}")
    )
