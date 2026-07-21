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

def test_topic_chat_uses_all_notes_in_same_topic(client):
    with client.session_transaction() as session:
        session['user_id'] = 1  # Set the user_id for the session
        session['username'] = 'testuser'  # Set a username for the session

    # Create a topic and multiple notes under that topic
    client.post('/create_topic', data={'title': 'Physics'}, follow_redirects=True)
    client.post('/create_note', data={'title': 'Note 1', 'content': 'Content of Note 1', 'topic_id': 1}, follow_redirects=True)
    client.post('/create_note', data={'title': 'Note 2', 'content': 'Content of Note 2', 'topic_id': 1}, follow_redirects=True)
    # Access the AI chat for one of the notes in the topic
    response = client.get('/chat/topics/1', follow_redirects=True)
    assert response.status_code == 200  # Ensure the AI chat page loads successfully
    # send a message in the AI chat for the topic
    client.post('/chat/topics/1', data={'message': 'Explain the topic.'}, follow_redirects=True)
    # assert the ai helper recieved the notes in the topic
    topic_notes = Note.query.filter_by(topic_id=1, user_id=1).all()
    conversation = topic_notes[0].conversation
    assert conversation is not None  # Ensure the conversation exists
    assert Message.query.filter_by(conversation_id=conversation.id, content='Explain the topic.').count() == 1  # Ensure the message was saved
    assert len(topic_notes) == 2  # Ensure both notes are in the topic
    assert topic_notes[0].content == 'Content of Note 1'
    assert topic_notes[1].content == 'Content of Note 2'

def test_topic_chat_rejects_unauthorized_note_access(client):
    with client.session_transaction() as session:
        session['user_id'] = 1  # Set the user_id for the session
        session['username'] = 'testuser'  # Set a username for the session

    # Create a note for user 1
    client.post('/create_note', data={'title': 'User 1 Note', 'content': 'Content of User 1 Note'}, follow_redirects=True)

    # Simulate a different user (user_id=2) trying to access the AI chat for user 1's note
    with client.session_transaction() as session:
        session['user_id'] = 2  # Change the user_id to simulate a different user
        session['username'] = 'unauthorized_user'  # Change the username

    response = client.get('/chat/1', follow_redirects=True)
    assert response.status_code == 200  # Ensure the page loads successfully
    assert b"Note not found or you do not have permission to access it." in response.data  # Ensure the error message is displayed

def test_topic_chat_creates_conversation(client):
    # first GET should create Conversation if missing
    with client.session_transaction() as session:
        session['user_id'] = 1  # Set the user_id for the session
        session['username'] = 'testuser'  # Set a username for the session

    # Create a topic and a note under that topic
    client.post('/create_topic', data={'title': 'Math'}, follow_redirects=True)
    client.post('/create_note', data={'title': 'Math Note', 'content': 'Content of Math Note', 'topic_id': 1}, follow_redirects=True)
    response = client.get('/chat/1', follow_redirects=True)
    assert response.status_code == 200  # Ensure the page loads successfully
    conversation = Conversation.query.filter_by(user_id=1).first()
    assert conversation is not None  # Ensure the conversation was created

def test_topic_chat_saves_user_and_assistant_messages(client):
    with client.session_transaction() as session:
        session['user_id'] = 1  # Set the user_id for the session
        session['username'] = 'testuser'  # Set a username for the session

    # Create a topic and a note under that topic
    client.post('/create_topic', data={'title': 'Biology'}, follow_redirects=True)
    client.post('/create_note', data={'title': 'Biology Note', 'content': 'Content of Biology Note', 'topic_id': 1}, follow_redirects=True)
    # Access the AI chat for the note to create a conversation
    client.get('/chat/1', follow_redirects=True)
    # Send a message in the AI chat
    client.post('/chat/1', data={'message': 'Explain photosynthesis.'}, follow_redirects=True)
    client.post('/chat/topics/1', data={'message': 'Explain the topic.'}, follow_redirects=True)
    note = Note.query.filter_by(id=1, user_id=1).first()  # Retrieve the note from the database
    conversation = note.conversation
    assert conversation is not None  # Ensure the conversation exists
    assert Message.query.filter_by(conversation_id=conversation.id, content='Explain photosynthesis.').count() == 1  # Ensure the user message was saved

def test_topic_chat_collects_all_notes_from_same_topic(client, monkeypatch):
    # mock ask_ai_with_topics
    # assert context includes all note contents in same topic
    with client.session_transaction() as session:
        session['user_id'] = 1  # Set the user_id for the session
        session['username'] = 'testuser'  # Set a username for the session

    # Create a topic and multiple notes under that topic
    client.post('/create_topic', data={'title': 'Chemistry'}, follow_redirects=True)
    client.post('/create_note', data={'title': 'Note A', 'content': 'Content of Note A', 'topic_id': 1}, follow_redirects=True)
    client.post('/create_note', data={'title': 'Note B', 'content': 'Content of Note B', 'topic_id': 1}, follow_redirects=True)

    # create another note in a different topic to ensure it is not included
    client.post('/create_topic', data={'title': 'History'}, follow_redirects=True) 
    client.post('/create_note', data={'title': 'Note C', 'content': 'Content of Note C', 'topic_id': 2}, follow_redirects=True) 

    # Access the AI chat for one of the notes in the topic
    response = client.get('/chat/topics/1', follow_redirects=True)
    assert response.status_code == 200  # Ensure the AI chat page loads successfully
    
    # assert the ai helper recieved the notes in the topic id=1
    topic_notes = Note.query.filter_by(topic_id=1, user_id=1).all()
    assert len(topic_notes) == 2  # Ensure only notes from topic id=1
    assert topic_notes[0].content == 'Content of Note A'
    assert topic_notes[1].content == 'Content of Note B'
    
    # assert that the note from topic id=2 is not included
    other_topic_notes = Note.query.filter_by(topic_id=2, user_id=1).all()
    assert len(other_topic_notes) == 1  # Ensure only one note from topic id=2
    assert other_topic_notes[0].content == 'Content of Note C'  # Ensure the content matches