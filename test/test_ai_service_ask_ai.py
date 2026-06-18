
from mailbox import Message

from app.models import Conversation
from app.services.ai_service import ask_ai


def test_ai_service_ask_ai():
    question = "What is AI?"
    note_content = "AI stands for Artificial Intelligence."
    response = ask_ai(question, note_content)
    assert response == f'You said: {question} Note content: {note_content}'

def test_ai_response():
    response = ask_ai("hello", "This is a note content.")
    assert response is not None

def test_note_content_in_response():
    question = "What is AI?"
    note_content = "AI stands for Artificial Intelligence."
    response = ask_ai(question, note_content)
    assert note_content == "AI stands for Artificial Intelligence." in response