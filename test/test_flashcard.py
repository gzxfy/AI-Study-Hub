from app.models.models import Flashcard
from conftest import client

def register_and_login(client, email='test@example.com', password='Password123!'):
    client.post('/register', data={'email': email, 'password': password, 'confirm_password': password}, follow_redirects=True)
    client.post('/login', data={'email': email, 'password': password}, follow_redirects=True)

def create_flashcard(client, user_id=None, topic_id=None, note_id=None, question='', answer='', difficulty=None):
    data = {
        'user_id': user_id,
        'topic_id': topic_id,
        'note_id': note_id,
        'question': question,
        'answer': answer,
        'difficulty': difficulty
    }
    return client.post('/createFlashcard', data=data, follow_redirects=True)

def create_note(client, user_id=None, topic_id=None, title='', content=''):
    data = {
        'user_id': user_id,
        'topic_id': topic_id,
        'title': title,
        'content': content
    }
    return client.post('/createNote', data=data, follow_redirects=True)

def test_create_flashcard(client):
    register_and_login(client)
    with client.session_transaction() as session:  # Ensure the session is available for the flashcard creation
        session['user_id'] = 1  # Set a dummy user_id for the session
        session['username'] = 'testuser'  # Set a dummy username for the session
    
    response = create_note(client, user_id=1, topic_id=None, title='Sample Note', content='Sample Content')
    response = create_flashcard(client, user_id=1, topic_id=None, note_id=1, question='Sample Question', answer='Sample Answer', difficulty='easy')
    assert b'Flashcard created successfully!' in response.data

    flashcard = Flashcard.query.filter_by(question='Sample Question').first()
    assert flashcard is not None
    assert flashcard.answer == 'Sample Answer'
    assert flashcard.difficulty == 'easy'

def test_create_flashcard_with_topic(client):
    register_and_login(client)
    with client.session_transaction() as session:
        session['user_id'] = 1
        session['username'] = 'testuser'
    
    response = create_note(client, user_id=1, topic_id=1, title='Sample Note with Topic', content='Sample Content')
    response = create_flashcard(client, user_id=1, topic_id=1, note_id=1, question='Sample Question with Topic', answer='Sample Answer with Topic', difficulty='medium')
    assert b'Flashcard created successfully!' in response.data

    flashcard = Flashcard.query.filter_by(question='Sample Question with Topic').first()
    assert flashcard is not None
    assert flashcard.answer == 'Sample Answer with Topic'
    assert flashcard.difficulty == 'medium'

def test_create_flashcard_without_topic(client):
    register_and_login(client)
    with client.session_transaction() as session:
        session['user_id'] = 1
        session['username'] = 'testuser'
    
    response = create_note(client, user_id=1, topic_id=None, title='Sample Note without Topic', content='Sample Content')
    response = create_flashcard(client, user_id=1, topic_id=None, note_id=1, question='Sample Question without Topic', answer='Sample Answer without Topic', difficulty='hard')
    assert b'Flashcard created successfully!' in response.data

    flashcard = Flashcard.query.filter_by(question='Sample Question without Topic').first()
    assert flashcard is not None
    assert flashcard.answer == 'Sample Answer without Topic'
    assert flashcard.difficulty == 'hard'

def test_create_flashcard_invalid_difficulty(client):
    register_and_login(client)
    with client.session_transaction() as session:
        session['user_id'] = 1
        session['username'] = 'testuser'
    
    response = create_note(client, user_id=1, topic_id=None, title='Sample Note Invalid Difficulty', content='Sample Content')
    response = create_flashcard(client, user_id=1, topic_id=None, note_id=1, question='Sample Question Invalid Difficulty', answer='Sample Answer Invalid Difficulty', difficulty='invalid')
    
    assert b"Difficulty must be &#39;easy&#39;, &#39;medium&#39;, or &#39;hard&#39; if provided." in response.data  # Assuming the flashcard creation route validates difficulty and flashes this message

def test_create_flashcard_missing_question(client):
    register_and_login(client)
    with client.session_transaction() as session:
        session['user_id'] = 1
        session['username'] = 'testuser'
    
    response = create_note(client, user_id=1, topic_id=None, title='Sample Note Missing Question', content='Sample Content')
    response = create_flashcard(client, user_id=1, topic_id=None, note_id=1, question='', answer='Sample Answer Missing Question', difficulty='easy')
    assert b'Question is required.' in response.data  # Assuming the flashcard creation route validates question and flashes this message

def test_create_flashcard_missing_answer(client):
    register_and_login(client)
    with client.session_transaction() as session:
        session['user_id'] = 1
        session['username'] = 'testuser'
    
    response = create_note(client, user_id=1, topic_id=None, title='Sample Note Missing Answer', content='Sample Content')
    response = create_flashcard(client, user_id=1, topic_id=None, note_id=1, question='Sample Question Missing Answer', answer='', difficulty='easy')
    assert b'Answer is required.' in response.data  # Assuming the flashcard creation route validates answer and flashes this message


def test_create_flashcard_question_too_long(client):
    register_and_login(client)
    with client.session_transaction() as session:
        session['user_id'] = 1
        session['username'] = 'testuser'

    response = create_note(client, user_id=1, topic_id=None, title='Sample Note Question Too Long', content='Sample Content')
    long_question = 'Q' * 501  # Assuming the question has a max length of 500 characters
    response = create_flashcard(client, user_id=1, topic_id=None, note_id=1, question=long_question, answer='Sample Answer Question Too Long', difficulty='easy')
    assert b'Question cannot be longer than 500 characters.' in response.data  # Assuming the flashcard creation route validates question length and flashes this message

def test_create_flashcard_answer_too_long(client):
    register_and_login(client)
    with client.session_transaction() as session:
        session['user_id'] = 1
        session['username'] = 'testuser'

    response = create_note(client, user_id=1, topic_id=None, title='Sample Note Answer Too Long', content='Sample Content')
    long_answer = 'A' * 2001  # Assuming the answer has a max length of 2000 characters
    response = create_flashcard(client, user_id=1, topic_id=None, note_id=1, question='Sample Question Answer Too Long', answer=long_answer, difficulty='easy')
    assert b'Answer cannot be longer than 2000 characters.' in response.data  # Assuming the flashcard creation route validates answer length and flashes this message