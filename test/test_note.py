def test_creating_note(client):
    # Set the user_id in the session
    with client.session_transaction() as session:
        session['user_id'] = 1

    response = client.post('/create', data={'title': 'Test Note', 'content': 'This is a test note.'}, follow_redirects=True)
    assert b'Note created successfully!' in response.data
    assert response.status_code == 200

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