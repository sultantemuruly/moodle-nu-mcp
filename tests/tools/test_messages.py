import asyncio
from typing import Any

from moodle_mcp.tools.messages import conversations


def test_private_conversation_named_after_member(moodle: Any) -> None:
    moodle.results["core_message_get_conversations"] = {
        "conversations": [
            {
                "id": 1,
                "name": "",
                "members": [{"fullname": "Ada Lovelace"}],
                "unreadcount": None,
                "messages": [{"text": "<p>Hi <b>there</b></p>", "timecreated": 0}],
            }
        ]
    }
    [conversation] = asyncio.run(conversations(moodle))
    assert (conversation.name, conversation.unread, conversation.last_message) == (
        "Ada Lovelace",
        0,
        "Hi there",
    )
