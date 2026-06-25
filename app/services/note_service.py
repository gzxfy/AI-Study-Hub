from app import db
from app.models.models import User, Conversation, Note, Topic, db, Message
import app.utils.validation_helpers as validation_helpers

def create_note(user_id, title, content, topic_id):
    validation_helpers.validate_note_data(title, content)
    new_note = Note(user_id=user_id, topic_id=topic_id, title=title, content=content)
    db.session.add(new_note)
    db.session.commit()
    return new_note

def view_note(note_id, user_id):
    note = Note.query.get(note_id)
    if not note:
        raise ValueError("Note not found!")
    if note.user_id != user_id:
        raise ValueError("You do not have permission to view this note!")
    return note

def delete_note(note_id, user_id):
    note = Note.query.get(note_id)
    if not note:
        raise ValueError("Note not found!")
    if note.user_id != user_id:
        raise ValueError("You do not have permission to delete this note!")
    db.session.delete(note)
    db.session.commit()

def edit_note(note_id, user_id, title, content):
    note = Note.query.get(note_id)
    if not note:
        raise ValueError("Note not found!")
    if note.user_id != user_id:
        raise ValueError("You do not have permission to edit this note!")
    validation_helpers.validate_note_data(title, content)
    note.title = title
    note.content = content
    db.session.commit()
    return note