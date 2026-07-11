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