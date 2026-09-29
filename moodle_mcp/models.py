from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Literal


def from_unix(timestamp: int) -> datetime:
    return datetime.fromtimestamp(timestamp, UTC)


@dataclass(frozen=True)
class Course:
    id: int
    name: str
    shortname: str
    url: str


@dataclass(frozen=True)
class Activity:
    id: int  # course-module id (cmid)
    module: str  # plugin key: resource, folder, url, assign, quiz, ...
    name: str
    url: str


@dataclass(frozen=True)
class Section:
    number: int
    title: str
    activities: list[Activity]


@dataclass(frozen=True)
class Deadline:
    name: str
    course: str
    module: str
    due: datetime
    overdue: bool
    url: str


@dataclass(frozen=True)
class GradeItem:
    name: str
    grade: str
    range: str
    percentage: str
    feedback: str


@dataclass(frozen=True)
class Material:
    name: str
    kind: Literal["file", "link"]
    url: str
    location: str  # "Section" or "Section/Folder", used as the download subdirectory


@dataclass(frozen=True)
class Conversation:
    id: int
    name: str
    unread: int
    last_message: str
    last_time: datetime | None


@dataclass(frozen=True)
class Notification:
    subject: str
    text: str
    time: datetime
    read: bool
    url: str
