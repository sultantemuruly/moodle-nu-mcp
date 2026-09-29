import asyncio
import json
from pathlib import Path
from typing import Any

from moodle_mcp.models import Material
from moodle_mcp.tools.materials import download_materials, list_materials

MOD = "https://moodle.nu.edu.kz/mod"
FILES = "https://moodle.nu.edu.kz/pluginfile.php"
SYLLABUS = f"{FILES}/1/mod_resource/content/1/Syllabus%20v2.pdf"
READING = f"{FILES}/2/mod_folder/content/0/Week%201/reading.pdf"


def setup(moodle: Any) -> None:
    cms = [
        ("1", "resource", "Syllabus"),
        ("2", "folder", "Readings"),
        ("3", "url", "Lecture video"),
        ("4", "forum", "Announcements"),
    ]
    moodle.results["core_courseformat_get_state"] = json.dumps(
        {
            "section": [
                {"number": 0, "title": "General", "cmlist": [c[0] for c in cms]}
            ],
            "cm": [
                {
                    "id": i,
                    "module": mod,
                    "name": name,
                    "url": f"{MOD}/{mod}/view.php?id={i}",
                    "uservisible": True,
                }
                for i, mod, name in cms
            ],
        }
    )
    moodle.results["core_course_get_enrolled_courses_by_timeline_classification"] = {
        "courses": [
            {"id": 5, "fullname": "Writing", "shortname": "WCS 150", "viewurl": ""}
        ]
    }
    moodle.redirects[f"{MOD}/resource/view.php?id=1&redirect=1"] = SYLLABUS
    moodle.redirects[f"{MOD}/url/view.php?id=3&redirect=1"] = "https://youtu.be/x"
    moodle.pages[f"{MOD}/folder/view.php?id=2"] = (
        f'<a href="{READING}?forcedownload=1">r</a>'
    )
    moodle.files = {SYLLABUS: b"syllabus", READING: b"reading"}


def test_list_materials(moodle: Any) -> None:
    setup(moodle)
    assert asyncio.run(list_materials(moodle, 5)) == [
        Material("Syllabus v2.pdf", "file", SYLLABUS, "General"),
        Material("reading.pdf", "file", READING, "General/Readings/Week 1"),
        Material("Lecture video", "link", "https://youtu.be/x", "General"),
    ]


def test_download_materials_saves_tree_and_skips_existing(
    moodle: Any, tmp_path: Path
) -> None:
    setup(moodle)
    root = tmp_path / "WCS 150"
    saved = asyncio.run(download_materials(moodle, 5, tmp_path))
    assert saved == [
        root / "General" / "Syllabus v2.pdf",
        root / "General" / "Readings" / "Week 1" / "reading.pdf",
    ]
    assert saved[1].read_bytes() == b"reading"
    assert (
        "- [Lecture video](https://youtu.be/x) — General"
        in (root / "links.md").read_text()
    )

    assert asyncio.run(download_materials(moodle, 5, tmp_path)) == []
    assert len(moodle.downloaded) == 2
