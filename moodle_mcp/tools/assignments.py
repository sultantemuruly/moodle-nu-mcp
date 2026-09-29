from moodle_mcp.client import MoodleClient
from moodle_mcp.parsers import parse_submission_status


async def assignment_status(m: MoodleClient, cmid: int) -> dict[str, str]:
    """Submission/grading status rows; due dates come from the deadline tools instead."""
    return parse_submission_status(
        await m.fetch_page(f"/mod/assign/view.php?id={cmid}")
    )
