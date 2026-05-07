from api_app.app import (
    ask_meeting_question,
    connect_integration,
    get_chat_messages,
    get_chat_sessions,
    get_meeting,
    get_meeting_action_items,
    get_meeting_summary,
    get_related_meetings,
    get_video_item,
    healthcheck,
    init_upload,
    search_meetings,
    sync_task,
)


def test_healthcheck():
    assert healthcheck()["status"] == "ok"


def test_related_meetings():
    assert get_related_meetings("mtg_123")["meetingId"] == "mtg_123"


def test_chat_question():
    assert ask_meeting_question("mtg_123", "What was decided?")["meetingId"] == "mtg_123"


def test_upload_init():
    result = init_upload("demo.mp4", "tenant_demo")
    assert result["method"] == "PUT"
    assert result["meetingId"].startswith("mtg_")
    assert result["videoItemId"].startswith("vid_")
    assert "tenant_demo" in result["s3Key"]
    assert "demo.mp4" in result["s3Key"]
    assert result["expiresIn"] == 3600


def test_get_meeting_and_summary():
    assert get_meeting("mtg_123")["id"] == "mtg_123"
    assert get_meeting_summary("mtg_123")["meetingId"] == "mtg_123"


def test_get_action_items_and_video_item():
    assert get_meeting_action_items("mtg_123")[0]["id"] == "ai_123"
    assert get_video_item("vid_123")["id"] == "vid_123"


def test_search_sessions_and_messages():
    assert search_meetings("authentication")["results"][0]["meetingId"] == "mtg_123"
    assert get_chat_sessions("mtg_123")[0]["id"] == "chat_session_001"
    assert get_chat_messages("chat_session_001")[0]["id"] == "msg_001"


def test_connect_and_sync():
    assert connect_integration("jira")["status"] == "connected"
    assert sync_task("task_123")["status"] == "sync_requested"
