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


def test_view_flashcard_by_id(client):
    register_and_login(client)
    with client.session_transaction() as session:
        session['user_id'] = 1
        session['username'] = 'testuser'

    response = create_note(client, user_id=1, topic_id=None, title='Sample Note View Flashcard', content='Sample Content')
    response = create_flashcard(client, user_id=1, topic_id=None, note_id=1, question='Sample Question View Flashcard', answer='Sample Answer View Flashcard', difficulty='easy')
    flashcard_id = 1  # Assuming this is the ID of the created flashcard
    response = client.get(f'/flashcard/{flashcard_id}')
    assert b'Sample Question View Flashcard' in response.data
    assert b'Sample Answer View Flashcard' in response.data

def test_view_all_flashcards(client):
    register_and_login(client)
    with client.session_transaction() as session:
        session['user_id'] = 1
        session['username'] = 'testuser'

    response = create_note(client, user_id=1, topic_id=None, title='Sample Note View All Flashcards', content='Sample Content')
    response = create_flashcard(client, user_id=1, topic_id=None, note_id=1, question='Sample Question View All Flashcards', answer='Sample Answer View All Flashcards', difficulty='easy')
    response = create_flashcard(client, user_id=1, topic_id=None, note_id=1, question='Another Sample Question View All Flashcards', answer='Another Sample Answer View All Flashcards', difficulty='easy')
    response = client.get('/flashcards')
    assert b"All Flashcards" in response.data  # Assuming the view_all_flashcards.html displays "All Flashcards" as a heading
    assert b'Sample Question View All Flashcards' in response.data
    assert b'Another Sample Question View All Flashcards' in response.data

def test_view_all_flashcards_no_flashcards(client):
    register_and_login(client)
    with client.session_transaction() as session:
        session['user_id'] = 1
        session['username'] = 'testuser'

    response = client.get('/flashcards')
    assert b"All Flashcards" in response.data  # Assuming the view_all_flashcards.html displays "All Flashcards" as a heading
    assert b'No flashcards available.' in response.data  # Assuming the view_all_flashcards.html displays this message when there are no flashcards

def test_view_flashcard_not_found(client):
    register_and_login(client)
    with client.session_transaction() as session:
        session['user_id'] = 1
        session['username'] = 'testuser'

    flashcard_id = 999  # Assuming this ID does not exist
    response = client.get(f'/flashcard/{flashcard_id}', follow_redirects=True)
    assert b'Flashcard not found.' in response.data  # Assuming the view_flashcard route flashes this message when the flashcard is not found
    assert response.status_code == 200  # Assuming the follow_redirects=True results in a 200 status code after redirection

def test_edit_flashcard(client):
    register_and_login(client)
    with client.session_transaction() as session:
        session['user_id'] = 1
        session['username'] = 'testuser'

    response = create_note(client, user_id=1, topic_id=None, title='Sample Note Edit Flashcard', content='Sample Content')
    response = create_flashcard(client, user_id=1, topic_id=None, note_id=1, question='Sample Question Edit Flashcard', answer='Sample Answer Edit Flashcard', difficulty='easy')
    flashcard_id = 1  # Assuming this is the ID of the created flashcard
    response = client.post(f'/editFlashcard/{flashcard_id}', data={
        'question': 'Updated Question Edit Flashcard',
        'answer': 'Updated Answer Edit Flashcard',
        'difficulty': 'medium'
    }, follow_redirects=True)
    assert b'Flashcard updated successfully!' in response.data  # Assuming the edit_flashcard route flashes this message upon successful update
    # Optionally, you can also verify that the flashcard's details have been updated by fetching the flashcard and checking its content
    response = client.get(f'/flashcard/{flashcard_id}')
    assert b'Updated Question Edit Flashcard' in response.data
    assert b'Updated Answer Edit Flashcard' in response.data
    flashcard = Flashcard.query.get(flashcard_id)
    assert flashcard.question == 'Updated Question Edit Flashcard'
    assert flashcard.answer == 'Updated Answer Edit Flashcard'
    assert flashcard.difficulty == 'medium'

def test_edit_flashcard_not_found(client):
    register_and_login(client)
    with client.session_transaction() as session:
        session['user_id'] = 1
        session['username'] = 'testuser'

    flashcard_id = 999  # Assuming this ID does not exist
    response = client.post(f'/editFlashcard/{flashcard_id}', data={
        'question': 'Updated Question Edit Flashcard',
        'answer': 'Updated Answer Edit Flashcard',
        'difficulty': 'medium'
    }, follow_redirects=True)
    assert b'Flashcard not found.' in response.data  # Assuming the edit_flashcard route flashes this message when the flashcard is not found
    assert response.status_code == 200  # Assuming the follow_redirects=True results in a 200 status code after redirection

def test_edit_only_question(client):
    register_and_login(client)
    with client.session_transaction() as session:
        session['user_id'] = 1
        session['username'] = 'testuser'
    
    response = create_note(client, user_id=1, topic_id=None, title='Sample Note Edit Flashcard', content='Sample Content')
    response = create_flashcard(client, user_id=1, topic_id=None, note_id=1, question='Sample Question Edit Flashcard', answer='Sample Answer Edit Flashcard', difficulty='easy')
    flashcard_id = 1  # Assuming this is the ID of the created flashcard
    response = client.post(f'/editFlashcard/{flashcard_id}', data={
        'question': 'Updated Question Only Edit Flashcard',
        'answer': 'Sample Answer Edit Flashcard',
        'difficulty': 'easy'
    }, follow_redirects=True)
    assert b'Flashcard updated successfully!' in response.data
    flashcard = Flashcard.query.get(flashcard_id)
    assert flashcard.question == 'Updated Question Only Edit Flashcard'
    assert flashcard.answer == 'Sample Answer Edit Flashcard'
    assert flashcard.difficulty == 'easy'

def test_edit_only_answer(client):
    register_and_login(client)
    with client.session_transaction() as session:
        session['user_id'] = 1
        session['username'] = 'testuser'
    
    response = create_note(client, user_id=1, topic_id=None, title='Sample Note Edit Flashcard', content='Sample Content')
    response = create_flashcard(client, user_id=1, topic_id=None, note_id=1, question='Sample Question Edit Flashcard', answer='Sample Answer Edit Flashcard', difficulty='easy')
    flashcard_id = 1  # Assuming this is the ID of the created flashcard
    response = client.post(f'/editFlashcard/{flashcard_id}', data={
        'question': 'Sample Question Edit Flashcard',
        'answer': 'Updated Answer Only Edit Flashcard',
        'difficulty': 'easy'
    }, follow_redirects=True)
    assert b'Flashcard updated successfully!' in response.data
    flashcard = Flashcard.query.get(flashcard_id)
    assert flashcard.question == 'Sample Question Edit Flashcard'
    assert flashcard.answer == 'Updated Answer Only Edit Flashcard'
    assert flashcard.difficulty == 'easy'

def test_edit_only_difficulty(client):
    register_and_login(client)
    with client.session_transaction() as session:
        session['user_id'] = 1
        session['username'] = 'testuser'

    response = create_note(client, user_id=1, topic_id=None, title='Sample Note Edit Flashcard', content='Sample Content')
    response = create_flashcard(client, user_id=1, topic_id=None, note_id=1, question='Sample Question Edit Flashcard', answer='Sample Answer Edit Flashcard', difficulty='easy')
    flashcard_id = 1  # Assuming this is the ID of the created flashcard
    response = client.post(f'/editFlashcard/{flashcard_id}', data={
        'question': 'Sample Question Edit Flashcard',
        'answer': 'Sample Answer Edit Flashcard',
        'difficulty': 'medium'
    }, follow_redirects=True)
    assert b'Flashcard updated successfully!' in response.data
    flashcard = Flashcard.query.get(flashcard_id)
    assert flashcard.question == 'Sample Question Edit Flashcard'
    assert flashcard.answer == 'Sample Answer Edit Flashcard'
    assert flashcard.difficulty == 'medium'