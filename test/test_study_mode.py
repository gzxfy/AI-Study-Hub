from app import db
from app.models.models import User, Note, Flashcard
def test_start_study_mode_returns_cards(client, test_app):
    user = User(username='testuser', email='test@example.com', password_hash='hashed-password')
    db.session.add(user)
    db.session.flush()

    note = Note(user_id=user.id, title='Test Note', content='This is a test note.')
    db.session.add(note)
    db.session.flush()

    db.session.add_all([
        Flashcard(user_id=user.id, note_id=note.id, question='Q1', answer='A1', difficulty='easy'),
        Flashcard(user_id=user.id, note_id=note.id, question='Q2', answer='A2', difficulty='easy'),
        Flashcard(user_id=user.id, note_id=note.id, question='Q3', answer='A3', difficulty='hard')
    ])
    db.session.commit()

    with client.session_transaction() as session:   
        session['user_id'] = user.id
        session['username'] = 'testuser'

    response = client.get(f'/study_mode/start?note_id={note.id}&difficulty=easy&card_count=2')
    data = response.get_json()

    assert response.status_code == 200
    assert len(data) == 2
    assert all(card['difficulty'] == 'easy' for card in data)

def test_review_study_mode_creates_progress(client, test_app):
    user = User(username='testuser2', email='test2@example.com', password_hash='hashed-password')
    db.session.add(user)
    db.session.flush()

    note = Note(user_id=user.id, title='Test Note 2', content='This is another test note.')
    db.session.add(note)
    db.session.flush()

    flashcard = Flashcard(user_id=user.id, note_id=note.id, question='Q1', answer='A1', difficulty='easy')
    db.session.add(flashcard)
    db.session.commit()

    with client.session_transaction() as session:
        session['user_id'] = user.id
        session['username'] = 'testuser2'

    payload = {
        'flashcard_id': flashcard.id,
        'marked_correctly': True
    }
    response = client.post('/study_mode/review', json=payload)
    data = response.get_json()

    assert response.status_code == 200
    assert data['flashcard_id'] == flashcard.id
    assert data['times_seen'] == 1
    assert data['times_correct'] == 1
    assert data['streak'] == 1
    assert data['progress'] == 1.0


def test_review_study_mode_returns_summary(client, test_app):
    with client.session_transaction() as session:
        session['user_id'] = 1
        session['username'] = 'testuser'

    response = client.post('/study_mode/end', json={
        'reviewed_results': [
            {'flashcard_id': 1, 'correct': True},
            {'flashcard_id': 2, 'correct': False},
            {'flashcard_id': 3, 'correct': True}
        ]
    })
    data = response.get_json()

    assert response.status_code == 200
    assert data['user_id'] == 1
    assert data['reviewed_count'] == 3
    assert data['correct_count'] == 2
    assert data['accuracy'] == 66.67

def test_unauthenticated_access(client):
    response = client.get('/study_mode/start?note_id=1')
    assert response.status_code == 302
    assert '/login' in response.headers['Location']

    response = client.post('/study_mode/review', json={'flashcard_id': 1, 'marked_correctly': True})
    assert response.status_code == 302
    assert '/login' in response.headers['Location']

    response = client.post('/study_mode/end', json={'reviewed_results': []})
    assert response.status_code == 302
    assert '/login' in response.headers['Location']

def test_invalid_card_count(client, test_app):
    user = User(username='testuser3', email='test@exampl;e.com', password_hash='hashed-password')
    db.session.add(user)
    db.session.flush()

    note = Note(user_id=user.id, title='Test Note 3', content='This is yet another test note.')
    db.session.add(note)
    db.session.flush()

    db.session.add_all([
        Flashcard(user_id=user.id, note_id=note.id, question='Q1', answer='A1', difficulty='easy'),
        Flashcard(user_id=user.id, note_id=note.id, question='Q2', answer='A2', difficulty='easy')
    ])
    db.session.commit()

    with client.session_transaction() as session:   
        session['user_id'] = user.id
        session['username'] = 'testuser3'

    response = client.get(f'/study_mode/start?note_id={note.id}&card_count=invalid')
    data = response.get_json()

    assert response.status_code == 400
    assert 'error' in data

def test_non_user_review(client, test_app):
    response = client.post('/study_mode/review', json={'flashcard_id': 999, 'marked_correctly': True})
    assert response.status_code == 302
    assert '/login' in response.headers['Location']

def test_empty_review_results(client, test_app):
    with client.session_transaction() as session:
        session['user_id'] = 1
        session['username'] = 'testuser'

    response = client.post('/study_mode/end', json={'reviewed_results': []})
    data = response.get_json()

    assert response.status_code == 200
    assert data['user_id'] == 1
    assert data['reviewed_count'] == 0
    assert data['correct_count'] == 0
    assert data['accuracy'] == 0