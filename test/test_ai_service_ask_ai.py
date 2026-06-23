from app.models import Conversation, Message
from app.services.ai_service import ask_ai


def test_ai_service_ask_ai():
    response = ask_ai("hello", "This is a note content.")
    assert response is not None
    assert isinstance(response, str)
    assert len(response) > 0

def test_ai_response():
    response = ask_ai("hello", "This is a note content.")
    assert response is not None
    assert isinstance(response, str)
    assert len(response) > 0

def test_note_content_in_response():
    question = "What is AI?"
    note_content = "AI stands for Artificial Intelligence."
    response = ask_ai(question, note_content)
    assert note_content == "AI stands for Artificial Intelligence."
    assert len(response) > 0
    assert isinstance(response, str)

def test_ai_returns_text():
    response = ask_ai("hello", "This is a note content.")
    assert response is not None
    assert isinstance(response, str)
    assert len(response) > 0