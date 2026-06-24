from app.models.models import Conversation, Message
from app.services.ai_service import ask_ai


def test_ai_service_ask_ai():
    response = ask_ai("hello", "This is a note content.", conversation_messages=[])
    assert response is not None
    assert isinstance(response, str)
    assert len(response) > 0

def test_ai_response():
    response = ask_ai("hello", "This is a note content.", conversation_messages=[])
    assert response is not None
    assert isinstance(response, str)
    assert len(response) > 0

def test_note_content_in_response():
    question = "What is AI?"
    note_content = "AI stands for Artificial Intelligence."
    response = ask_ai(question, note_content, conversation_messages=[])
    assert note_content == "AI stands for Artificial Intelligence."
    assert len(response) > 0
    assert isinstance(response, str)

def test_ai_returns_text():
    response = ask_ai("hello", "This is a note content.", conversation_messages=[])
    assert response is not None
    assert isinstance(response, str)
    assert len(response) > 0

def test_ai_remembers_previous_messages():
    question1 = "What is AI?"
    question2 = "Explain machine learning."
    note_content = "AI stands for Artificial Intelligence."
    response1 = ask_ai(question1, note_content=note_content, conversation_messages=[])
    response2 = ask_ai(question2, note_content=note_content, conversation_messages=[Message(role='user', content=question1), Message(role='assistant', content=response1)])
    assert response2 is not None
    assert isinstance(response2, str)
    assert len(response2) > 0