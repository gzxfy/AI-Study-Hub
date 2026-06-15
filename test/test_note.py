from app.models import Note


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