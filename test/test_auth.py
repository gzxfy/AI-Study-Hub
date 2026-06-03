from flask import session

def register(client, username, password):
    return client.post('/register', data={
        'username': username,
        'password': password,
        'confirm_password': password
    }, follow_redirects=True)

def test_register(client):
    response = client.get('/register', data={
        'username': 'testuser',
        'password': 'testpassword',
        'confirm_password': 'testpassword'
    })
    assert response.status_code == 200

def test_mismatched_passwords(client):
    response = client.post('/register', data={
        'username': 'testuser2',
        'password': 'testpassword',
        'confirm_password': 'wrongpassword'
    }, follow_redirects=True)
    assert b'Passwords must match' in response.data

def test_duplicate_username(client):
    response = client.post('/register', data={
        'username': 'testuser3',
        'password': 'testpassword',
        'confirm_password': 'testpassword'
    }, follow_redirects=True)
    assert b'Username already exists' in response.data


