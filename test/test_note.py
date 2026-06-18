from email.message import Message

from app.models import Conversation, Note, Topic, Message


def test_creating_note(client):
    # Set the user_id in the session
    with client.session_transaction() as session:
        session['user_id'] = 1

    response = client.post('/create', data={'title': 'Test Note', 'content': 'This is a test note.'}, follow_redirects=True)
    assert b'Note created successfully!' in response.data
    assert response.status_code == 200

    note = Note.query.filter_by(user_id=1, title='Test Note').first()
    assert note is not None
    assert note.content == 'This is a test note.'
    assert note.user_id == 1

def test_empty_Title_creation(client):
    # Set the user_id in the session
    with client.session_transaction() as session:
        session['user_id'] = 1

    response = client.post('/create', data={'title': '', 'content': 'This is a test content.'}, follow_redirects=True)
    assert b'Title is required.' in response.data
    assert response.status_code == 200

def test_empty_content_creation(client):
    # Set the user_id in the session
    with client.session_transaction() as session:
        session['user_id'] = 1

    response = client.post('/create', data={'title': 'Test Title', 'content': ''}, follow_redirects=True)
    assert b'Content is required.' in response.data
    assert response.status_code == 200

def test_title_length_exceeds_limit(client):
    # Set the user_id in the session
    with client.session_transaction() as session:
        session['user_id'] = 1

    long_title = 'T' * 101  # Title with 101 characters
    response = client.post('/create', data={'title': long_title, 'content': 'This is a test content.'}, follow_redirects=True)
    assert b'Title cannot be longer than 100 characters.' in response.data
    assert response.status_code == 200

def test_content_length_exceeds_limit(client):
    # Set the user_id in the session
    with client.session_transaction() as session:
        session['user_id'] = 1

    long_content = 'C' * 2001  # Content with 2001 characters
    response = client.post('/create', data={'title': 'Test Title', 'content': long_content}, follow_redirects=True)
    assert b'Content cannot be longer than 2000 characters.' in response.data
    assert response.status_code == 200

def test_view_note_not_found(client):
    # Set the user_id in the session
    with client.session_transaction() as session:
        session['user_id'] = 1

    response = client.get('/view/9999', follow_redirects=True)  # Assuming 9999 is a non-existent note_id
    assert b'Note not found!' in response.data
    assert response.status_code == 200

def test_view_note(client):
    with client.session_transaction() as session:
        session['user_id'] = 1

    response = client.post('/create', data={'title': 'Test Note', 'content': 'This is a test note.'}, follow_redirects=True)
    response = client.get('/view/1', follow_redirects=True)  # Assuming 1 is an existing note_id
    assert b'Test Note' in response.data  # Assuming the note with ID 1 has the title 'Test Note'
    assert b'This is a test note.' in response.data  # Assuming the note with ID 1 has the content 'This is a test note.'
    assert response.status_code == 200

def test_delete_note(client):
    with client.session_transaction() as session:
        session['user_id'] = 1

    response = client.post('/create', data={'title': 'Test Note', 'content': 'This is a test note.'}, follow_redirects=True)
    response = client.get('/delete/1', follow_redirects=True)  # Assuming 1 is an existing note_id
    assert b'Note deleted successfully!' in response.data
    assert response.status_code == 200

    note = Note.query.get(1)
    assert note is None  # The note should be deleted and no longer exist in the database

def test_edit_note(client):
    with client.session_transaction() as session:
        session['user_id'] = 1

    response = client.post('/create', data={'title': 'Test Note', 'content': 'This is a test note.'}, follow_redirects=True)
    response = client.post('/edit/1', data={'title': 'Updated Test Note', 'content': 'This is an updated test note.'}, follow_redirects=True)  # Assuming 1 is an existing note_id
    assert b'Note updated successfully!' in response.data
    assert response.status_code == 200

    note = Note.query.get(1)  # Retrieve the note with ID 1 from the database
    assert note.title == 'Updated Test Note'  # The note's title should be updated
    assert note.content == 'This is an updated test note.'  # The note's content should be updated

    response = client.get('/view/1', follow_redirects=True)
    assert b'Updated Test Note' in response.data  # Assuming the note with ID 1 has the updated title
    assert b'This is an updated test note.' in response.data  # Assuming the note with ID 1 has the updated content
    assert response.status_code == 200

def test_unauthorization_edit_note(client):
    with client.session_transaction() as session:
        session['user_id'] = 1

    response = client.post('/create', data={'title': 'Test Note', 'content': 'This is a test note.'}, follow_redirects=True)
    with client.session_transaction() as session:
        session['user_id'] = 2  # Switch to a different user
    response = client.post('/edit/1', data={'title': 'Hacked Note', 'content': 'This is a hacked note.'}, follow_redirects=True)
    assert b'You do not have permission to edit this note!' in response.data
    assert response.status_code == 200

def test_unauthorization_delete_note(client):
    with client.session_transaction() as session:
        session['user_id'] = 1

    response = client.post('/create', data={'title': 'Test Note', 'content': 'This is a test note.'}, follow_redirects=True)
    with client.session_transaction() as session:
        session['user_id'] = 2  # Switch to a different user
    response = client.get('/delete/1', follow_redirects=True)
    assert b'You do not have permission to delete this note!' in response.data
    assert response.status_code == 200

def test_dashboard_with_zero_notes(client):
    with client.session_transaction() as session:
        session['user_id'] = 1  # Set the user_id for the session
        session['username'] = 'testuser'  # Set a username for the session
    response = client.get('/')
    assert Note.query.filter_by(user_id=1).count() == 0  # Ensure there are no notes for the user
    assert b'No notes yet' in response.data  # Assuming the dashboard shows this message when there are no notes
    assert response.status_code == 200

def test_dashboard_with_notes(client):
    with client.session_transaction() as session:
        session['user_id'] = 1  # Set the user_id for the session
        session['username'] = 'testuser'  # Set a username for the session
    # Create a note for the user
    response = client.post('/create', data={'title': 'Test Note', 'content': 'This is a test note.'}, follow_redirects=True)
    response = client.get('/')
    assert Note.query.filter_by(user_id=1).count() > 0  # Ensure there are notes for the user
    assert b'Test Note' in response.data  # Assuming the dashboard shows the note title
    assert response.status_code == 200

def test_dashboard_displays_five_notes(client):
    with client.session_transaction() as session:
        session['user_id'] = 1  # Set the user_id for the session
        session['username'] = 'testuser'  # Set a username for the session
    # Create six notes for the user
    for i in range(6):
        client.post('/create', data={'title': f'Test Note {i+1}', 'content': f'This is test note {i+1}.'}, follow_redirects=True)
    response = client.get('/')
    assert Note.query.filter_by(user_id=1).count() >= 5  # Ensure there are at least five notes for the user
    for i in range(6, 1, -1):  # Check that the five most recent notes are displayed
        assert f'Test Note {i}'.encode() in response.data
    assert response.status_code == 200

def test_note_in_topic(client):
    with client.session_transaction() as session:
        session['user_id'] = 1  # Set the user_id for the session
        session['username'] = 'testuser'  # Set a username for the session
    # Create a topic for the user
    response = client.post('/topic/create', data={'title': 'Test Topic', 'description': 'This is a test topic.', 'color': '#ffffff'}, follow_redirects=True)
    topic = Topic.query.filter_by(user_id=1).first()
    # Create a note within the topic
    response = client.post('/create', data={'title': 'Note in Topic', 'content': 'This note is in a topic.', 'topic_id': topic.id}, follow_redirects=True)
    assert Note.query.filter_by(topic_id=topic.id).count() == 1  # Ensure the note is associated with the topic
    assert b'Note in Topic' in response.data  # Assuming the note title is displayed after creation

def test_note_without_topic(client):
    with client.session_transaction() as session:
        session['user_id'] = 1  # Set the user_id for the session
        session['username'] = 'testuser'  # Set a username for the session
    # Create a note without specifying a topic
    response = client.post('/create', data={'title': 'Note without Topic', 'content': 'This note has no topic.'}, follow_redirects=True)
    note = Note.query.filter_by(user_id=1, topic_id=None).first()
    assert note is not None  # Ensure the note is created without a topic
    assert b'Note without Topic' in response.data  # Assuming the note title is displayed after creation

def test_search_notes(client):
    with client.session_transaction() as session:
        session['user_id'] = 1  # Set the user_id for the session
        session['username'] = 'testuser'  # Set a username for the session
    # Create a note to search for
    client.post('/create', data={'title': 'Searchable Note', 'content': 'This note can be searched.'}, follow_redirects=True)
    # Search for the note by title
    response = client.get('/search?q=Searchable&type=notes', follow_redirects=True)
    assert b'Searchable Note' in response.data  # Ensure the note is found in the search results
    assert response.status_code == 200  # Ensure the search request was successful

def test_search_topics(client):
    with client.session_transaction() as session:
        session['user_id'] = 1  # Set the user_id for the session
        session['username'] = 'testuser'  # Set a username for the session
    # Create a topic to search for
    client.post('/topic/create', data={'title': 'Searchable Topic', 'description': 'This topic can be searched.', 'color': '#ffffff'}, follow_redirects=True)
    # Search for the topic by title
    response = client.get('/search?q=Searchable&type=topics', follow_redirects=True)
    assert b'Searchable Topic' in response.data  # Ensure the topic is found in the search results
    assert response.status_code == 200  # Ensure the search request was successful

def test_search_no_results(client):
    with client.session_transaction() as session:
        session['user_id'] = 1  # Set the user_id for the session
        session['username'] = 'testuser'  # Set a username for the session
    # Search for a non-existent note
    response = client.get('/search?q=NonExistent&type=notes', follow_redirects=True)
    assert b'No results found' in response.data  # Ensure the no results message is shown
    assert response.status_code == 200  # Ensure the search request was successful

def test_ai_chat_loads(client):
    response = client.get('/chat/1', follow_redirects=True)
    assert response.status_code == 200  # Ensure the AI chat page loads successfully

def test_conversation_created(client):
    with client.session_transaction() as session:
        session['user_id'] = 1  # Set the user_id for the session
        session['username'] = 'testuser'  # Set a username for the session

    client.post('/create', data={'title': 'Searchable Note', 'content': 'This note can be searched.'}, follow_redirects=True)

    # Access the AI chat for a note, which should create a conversation if it doesn't exist
    response = client.get('/chat/1', follow_redirects=True)
    assert response.status_code == 200  # Ensure the AI chat page loads successfully
    assert Conversation.query.count() == 1  # Ensure a conversation was created for the note

def test_message_being_saved(client):
    with client.session_transaction() as session:
        session['user_id'] = 1  # Set the user_id for the session
        session['username'] = 'testuser'  # Set a username for the session

    client.post('/create', data={'title': 'Message Test Note', 'content': 'This note is for testing messages.'}, follow_redirects=True)

    # Access the AI chat for the note to create a conversation
    client.get('/chat/1', follow_redirects=True)

    # Send a message in the AI chat
    client.post('/chat/1', data={'message': 'Hello AI!'}, follow_redirects=True)
    print(Message.query.filter_by(conversation_id=1).all())
    print(len(Message.query.filter_by(conversation_id=1).all()))

    # Ensure the message was saved in the database
    conversation = Conversation.query.filter_by(note_id=1).first()
    assert conversation is not None  # Ensure the conversation exists
    assert Message.query.filter_by(conversation_id=conversation.id, content='Hello AI!').count() == 1  # Ensure the message was saved

def test_assistant_message_being_saved(client):
    with client.session_transaction() as session:
        session['user_id'] = 1  # Set the user_id for the session
        session['username'] = 'testuser'  # Set a username for the session

    client.post('/create', data={'title': 'Assistant Message Test Note', 'content': 'This note is for testing assistant messages.'}, follow_redirects=True)

    # Access the AI chat for the note to create a conversation
    client.get('/chat/1', follow_redirects=True)

    # Send a message in the AI chat to trigger an assistant response
    client.post('/chat/1', data={'message': 'Hello AI!'}, follow_redirects=True)

    # Ensure the assistant message was saved in the database
    conversation = Conversation.query.filter_by(note_id=1).first()
    assert conversation is not None  # Ensure the conversation exists
    assert Message.query.filter_by(conversation_id=conversation.id, role='assistant').count() == 1  # Ensure the assistant message was saved
