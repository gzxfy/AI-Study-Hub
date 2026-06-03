
def register(client, username, password):
    return client.post('/register', data={
        'username': username,
        'password': password,
        'confirm_password': password
    }, follow_redirects=True)

def test_register(client):
    response = client.post('/register', data={
        'email': 'testuser@example.com',
        'password': 'TestPassword1!',
        'confirm_password': 'TestPassword1!'
    })
    assert response.status_code == 200

def test_mismatched_passwords(client):
    response = client.post('/register', data={
        'email': 'testuser2@example.com',
        'password': 'TestPassword1!',
        'confirm_password': 'WrongPassword1!'
    }, follow_redirects=True)
    assert b'Passwords do not match' in response.data

def test_duplicate_email(client):
    data = {
        'email': 'testuser@example.com',
        'password': 'TestPassword1!',
        'confirm_password': 'TestPassword1!'
    }
    client.post('/register', data=data, follow_redirects=True)  # First registration
    response = client.post('/register', data=data, follow_redirects=True)
    assert b'Email already registered' in response.data


