"""Pure HTML → data parsers for Moodle pages that service.php won't serve; see docs/data-access.md."""

from selectolax.parser import HTMLParser, Node

from moodle_mcp.models import GradeItem

_SKIPPED_STATUS_ROWS = {"Submission comments"}  # holds a JS comment template, not data


def _text(node: Node | None) -> str:
    return node.text(separator=" ", strip=True) if node else ""


def parse_folder_files(html: str) -> list[str]:
    """Unique pluginfile URLs in a mod/folder page, in page order."""
    urls = (
        a.attributes.get("href") or ""
        for a in HTMLParser(html).css("a[href*='/pluginfile.php/']")
    )
    return list(dict.fromkeys(url.split("?")[0] for url in urls))


def parse_submission_status(html: str) -> dict[str, str]:
    """Rows of an assignment's submission status table, e.g. {"Grading status": "Not graded"}."""
    rows = HTMLParser(html).css(".submissionstatustable tr")
    pairs = ((_text(tr.css_first("th")), _text(tr.css_first("td"))) for tr in rows)
    return {
        key: value for key, value in pairs if key and key not in _SKIPPED_STATUS_ROWS
    }


def parse_grade_items(html: str) -> list[GradeItem]:
    """Grade rows of the user grade report; category header rows have no grade cell and are skipped."""
    items = []
    for tr in HTMLParser(html).css("table.user-grade tr"):
        grade = tr.css_first("td.column-grade")
        if grade is None:
            continue
        name = tr.css_first("th.column-itemname")
        items.append(
            GradeItem(
                name=_text(name.css_first(".rowtitle") if name else None)
                or _text(name),
                grade=_text(grade.css_first("div > div")) or _text(grade),
                range=_text(tr.css_first("td.column-range")),
                percentage=_text(tr.css_first("td.column-percentage")),
                feedback=_text(tr.css_first("td.column-feedback")),
            )
        )
    return items


def html_to_text(html: str) -> str:
    return HTMLParser(html).text(separator=" ", strip=True)
