from moodle_mcp.client import MoodleClient
from moodle_mcp.models import Conversation, Notification, from_unix
from moodle_mcp.parsers import html_to_text


async def conversations(m: MoodleClient, limit: int = 20) -> list[Conversation]:
    data = await m.call(
        "core_message_get_conversations", {"userid": m.userid, "limitnum": limit}
    )
    return [
        Conversation(
            id=c["id"],
            # Private chats have no name; show the other member instead.
            name=c["name"] or ", ".join(u["fullname"] for u in c["members"]),
            unread=c["unreadcount"] or 0,
            last_message=html_to_text(c["messages"][0]["text"])
            if c["messages"]
            else "",
            last_time=from_unix(c["messages"][0]["timecreated"])
            if c["messages"]
            else None,
        )
        for c in data["conversations"]
    ]


async def notifications(m: MoodleClient, limit: int = 20) -> list[Notification]:
    data = await m.call(
        "message_popup_get_popup_notifications", {"useridto": m.userid, "limit": limit}
    )
    return [
        Notification(
            subject=n["subject"],
            text=n["smallmessage"],
            time=from_unix(n["timecreated"]),
            read=n["read"],
            url=n["contexturl"] or "",
        )
        for n in data["notifications"]
    ]
