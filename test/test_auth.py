
# =====REGISTER TESTS=====
def test_register_form_includes_csrf_token(client):
    response = client.get('/register')
    assert response.status_code == 200
    assert b'name="csrf_token"' in response.data


def test_register(client):
    response = client.post('/register', data={
        'username': 'testuser',
        'email': 'testuser@example.com',
        'password': 'TestPassword1!',
        'confirm_password': 'TestPassword1!'
    }, follow_redirects=True)
    assert response.status_code == 200

def test_mismatched_passwords(client):
    response = client.post('/register', data={
        'username': 'testuser2',
        'email': 'testuser2@example.com',
        'password': 'TestPassword1!',
        'confirm_password': 'WrongPassword1!'
    }, follow_redirects=True)
    assert b'Passwords do not match' in response.data

def test_duplicate_email(client):
    data = {
        'username': 'testuser',
        'email': 'testuser@example.com',
        'password': 'TestPassword1!',
        'confirm_password': 'TestPassword1!'
    }
    client.post('/register', data=data, follow_redirects=True)  # First registration
    response = client.post('/register', data=data, follow_redirects=True)
    assert b'Email already registered' in response.data

# =====LOGIN TESTS=====
def test_login_form_includes_csrf_token(client):
    response = client.get('/login')
    assert response.status_code == 200
    assert b'name="csrf_token"' in response.data


def test_login(client):
    # First, register a user to log in with
    client.post('/register', data={
        'username': 'loginuser',
        'email': 'loginuser@example.com',
        'password': 'TestPassword1!',
        'confirm_password': 'TestPassword1!'
    }, follow_redirects=True)

    response = client.post('/login', data={
        'email': 'loginuser@example.com',
        'password': 'TestPassword1!'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b'Login successful! Welcome back.' in response.data

def test_invalid_login(client):
    client.post('/register', data={
        'username': 'testuser',
        'email': 'loginuser@example.com',
        'password': 'TestPassword1!',
        'confirm_password': 'TestPassword1!'
    }, follow_redirects=True)

    response = client.post('/login', data={
        'email': 'testuser@example.com',
        'password': 'WrongPassword1!'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b'Invalid email or password.' in response.data

def test_empty_email_login(client):
    response = client.post('/login', data={
        'email': '',
        'password': 'TestPassword1!'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b'Email is required.' in response.data

def test_empty_password_login(client):
    response = client.post('/login', data={
        'email': 'testuser@example.com',
        'password': ''
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b'Password is required.' in response.data
