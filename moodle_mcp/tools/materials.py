"""Course files and links posted by instructors, and downloading them to disk."""

import asyncio
import re
from pathlib import Path
from urllib.parse import unquote, urlparse

from moodle_mcp.client import MoodleClient
from moodle_mcp.config import DOWNLOAD_DIR
from moodle_mcp.models import Activity, Material
from moodle_mcp.parsers import parse_folder_files
from moodle_mcp.tools.courses import course_contents, list_courses


def _filename(url: str) -> str:
    return unquote(urlparse(url).path.rsplit("/", 1)[-1])


def _folder_subdir(url: str) -> str:
    # .../mod_folder/content/<rev>/<sub/dirs>/<file>: keep the folder's own subdirectories.
    inner = unquote(urlparse(url).path).split("/content/", 1)[1].split("/")[1:-1]
    return "".join(f"/{d}" for d in inner)


def _safe(part: str) -> str:
    return re.sub(r'[\\/:*?"<>|]+', "_", part).strip(" .")[:100] or "_"


async def _materials_of(
    m: MoodleClient, activity: Activity, location: str
) -> list[Material]:
    # `redirect=1` makes resource/url answer with a 303 to the file / external target.
    match activity.module:
        case "resource":
            url = await m.resolve_redirect(f"{activity.url}&redirect=1")
            return [Material(_filename(url), "file", url, location)]
        case "folder":
            urls = parse_folder_files(await m.fetch_page(activity.url))
            return [
                Material(
                    _filename(u),
                    "file",
                    u,
                    f"{location}/{activity.name}{_folder_subdir(u)}",
                )
                for u in urls
            ]
        case "url":
            url = await m.resolve_redirect(f"{activity.url}&redirect=1")
            return [Material(activity.name, "link", url, location)]
        case _:
            return []


async def list_materials(m: MoodleClient, course_id: int) -> list[Material]:
    """Files (resource, folder contents) and external links (url) of a course, in course order."""
    jobs = [
        _materials_of(m, activity, section.title)
        for section in await course_contents(m, course_id)
        for activity in section.activities
    ]
    return [material for batch in await asyncio.gather(*jobs) for material in batch]


async def download_materials(
    m: MoodleClient, course_id: int, dest: Path = DOWNLOAD_DIR
) -> list[Path]:
    """Save course files under dest/<course>/<section>/..., skipping existing ones; returns new paths.

    External links are listed in dest/<course>/links.md.
    """
    course = next((c for c in await list_courses(m, "all") if c.id == course_id), None)
    root = dest / _safe(course.shortname if course else str(course_id))
    materials = await list_materials(m, course_id)
    saved = []
    for material in (x for x in materials if x.kind == "file"):
        path = root.joinpath(
            *map(_safe, material.location.split("/")), _safe(material.name)
        )
        if path.exists():
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(await m.download(material.url))
        saved.append(path)
    if links := [x for x in materials if x.kind == "link"]:
        root.mkdir(parents=True, exist_ok=True)
        (root / "links.md").write_text(
            "".join(f"- [{x.name}]({x.url}) — {x.location}\n" for x in links)
        )
    return saved
