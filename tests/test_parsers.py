from moodle_mcp.models import GradeItem
from moodle_mcp.parsers import (
    html_to_text,
    parse_folder_files,
    parse_grade_items,
    parse_submission_status,
)

BASE = "https://moodle.nu.edu.kz/pluginfile.php/1/mod_folder/content/0"


def test_parse_folder_files_dedupes_and_strips_query() -> None:
    html = f"""
        <a href="{BASE}/Week%201/a.pdf">a</a>
        <a href="{BASE}/Week%201/a.pdf?forcedownload=1">download</a>
        <a href="{BASE}/b.docx">b</a>
        <a href="https://moodle.nu.edu.kz/course/view.php?id=1">course</a>"""
    assert parse_folder_files(html) == [f"{BASE}/Week%201/a.pdf", f"{BASE}/b.docx"]


def test_parse_submission_status_skips_comments() -> None:
    html = """<div class="submissionstatustable"><table><tbody>
        <tr><th>Submission status</th><td>Submitted for grading</td></tr>
        <tr><th>Grading status</th><td class="submissionnotgraded">Not graded</td></tr>
        <tr><th>Submission comments</th><td><div id="cmt-tmpl">___content___</div></td></tr>
    </tbody></table></div>"""
    assert parse_submission_status(html) == {
        "Submission status": "Submitted for grading",
        "Grading status": "Not graded",
    }


def test_parse_grade_items() -> None:
    html = """<table class="user-grade"><tbody>
        <tr><th class="level1 category column-itemname">Calculus III</th></tr>
        <tr>
          <th class="level2 item column-itemname"><span class="d-block">External tool</span>
            <div class="rowtitle"><a>Set 1</a></div></th>
          <td class="column-grade"><div class="d-flex"><div>15.00</div>
            <div class="ps-1"><div class="action-menu"><a aria-label="Actions">Grade analysis</a></div></div></div></td>
          <td class="column-range">0–15</td><td class="column-percentage">100.00 %</td>
          <td class="column-feedback">Well done</td>
        </tr>
        <tr>
          <th class="level1 courseitem column-itemname">Course total</th>
          <td class="column-grade">-</td><td class="column-range">0–100</td>
          <td class="column-percentage">-</td><td class="column-feedback"></td>
        </tr>
    </tbody></table>"""
    assert parse_grade_items(html) == [
        GradeItem("Set 1", "15.00", "0–15", "100.00 %", "Well done"),
        GradeItem("Course total", "-", "0–100", "-", ""),
    ]


def test_html_to_text() -> None:
    assert html_to_text("<p>Hello <b>there</b></p>") == "Hello there"
