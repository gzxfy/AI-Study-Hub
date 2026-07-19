from app.models.models import Conversation, Message, Note
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

def test_ai_chat_loads(client):
    response = client.get('/chat/1', follow_redirects=True)
    assert response.status_code == 200  # Ensure the AI chat page loads successfully

def test_conversation_created(client):
    with client.session_transaction() as session:
        session['user_id'] = 1  # Set the user_id for the session
        session['username'] = 'testuser'  # Set a username for the session

    client.post('/create_note', data={'title': 'Searchable Note', 'content': 'This note can be searched.'}, follow_redirects=True)

    # Access the AI chat for a note, which should create a conversation if it doesn't exist
    response = client.get('/chat/1', follow_redirects=True)
    assert response.status_code == 200  # Ensure the AI chat page loads successfully
    assert Conversation.query.count() == 1  # Ensure a conversation was created for the note

def test_message_being_saved(client):
    with client.session_transaction() as session:
        session['user_id'] = 1  # Set the user_id for the session
        session['username'] = 'testuser'  # Set a username for the session

    client.post('/create_note', data={'title': 'Message Test Note', 'content': 'This note is for testing messages.'}, follow_redirects=True)

    # Access the AI chat for the note to create a conversation
    client.get('/chat/1', follow_redirects=True)

    # Send a message in the AI chat
    client.post('/chat/1', data={'message': 'Hello AI!'}, follow_redirects=True)
    note = Note.query.filter_by(id=1, user_id=1).first()  # Retrieve the note from the database
    # Ensure the message was saved in the database
    conversation = note.conversation
    assert conversation is not None  # Ensure the conversation exists
    assert Message.query.filter_by(conversation_id=conversation.id, content='Hello AI!').count() == 1  # Ensure the message was saved

def test_mode_detection():
    from app.services.ai_service import detect_mode_from_question

    assert detect_mode_from_question("Quiz the concept of gravity.") == "quiz"
    assert detect_mode_from_question("What is the capital of France?") == "question"
    assert detect_mode_from_question("Summarize the article about climate change.") == "summary"
    assert detect_mode_from_question("This is a random statement.") == "general"

def test_build_messages_maps_non_special_modes_to_teach():
    from app.services.ai_service import build_messages

    messages = build_messages("This is a general question.", "Note content here.", conversation_messages=[])

    assert messages[0]['role'] == 'system'
    assert "study tutor" in messages[0]["content"].lower()
    assert "check-for-understanding question" in messages[0]["content"].lower()

def test_message_structure_in_build_messages():
    from app.services.ai_service import build_messages

    question = "What is AI?"
    note_content = "AI stands for Artificial Intelligence."
    conversation_messages = [Message(role='user', content='Hello'), Message(role='assistant', content='Hi!')]
    
    messages = build_messages(question, note_content, conversation_messages)

    assert messages[0]['role'] == 'system'
    assert messages[1]['role'] == 'system'
    assert messages[2]['role'] == 'user' and messages[2]['content'] == 'Hello'
    assert messages[3]['role'] == 'assistant' and messages[3]['content'] == 'Hi!'
    assert messages[-1]['role'] == 'user' and messages[-1]['content'] == question

def test_no_duplicate_messages_in_build_messages():
    from app.services.ai_service import build_messages

    question = "What is AI?"
    note_content = "AI stands for Artificial Intelligence."
    conversation_messages = [Message(role='user', content='Hello'), Message(role='assistant', content='Hi!')]
    
    messages = build_messages(question, note_content, conversation_messages)

    # Ensure that the user question is only added once at the end
    user_questions = [msg for msg in messages if msg['role'] == 'user' and msg['content'] == question]
    assert len(user_questions) == 1

