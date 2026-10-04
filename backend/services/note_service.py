from backend import db
from backend.models.models import Note, Topic
import backend.utils.validation_helpers as validation_helpers
import backend.services.pdf_service as pdf_service


class InvalidTopicError(ValueError):
    """Raised when a note references a topic the user cannot access."""


def list_notes(user_id):
    """Return a user's notes, newest updates first."""
    return (
        Note.query
        .filter_by(user_id=user_id)
        .order_by(Note.updated_at.desc(), Note.id.desc())
        .all()
    )


def list_topics(user_id):
    """Return the topics owned by a user for note assignment."""
    return Topic.query.filter_by(user_id=user_id).order_by(Topic.title.asc()).all()


def topic_belongs_to_user(topic_id, user_id):
    """Check that a topic exists and belongs to the requesting user."""
    return Topic.query.filter_by(id=topic_id, user_id=user_id).first() is not None


def create_note(user_id, title, content, topic_id, uploaded_pdf_path=None):
    """Extract optional PDF text, validate it, and save a study note."""
    if topic_id is not None and not topic_belongs_to_user(topic_id, user_id):
        raise InvalidTopicError("Topic is invalid or unavailable.")

    extracted_text = ""
    uploaded_pdf_name = None

    if uploaded_pdf_path and getattr(uploaded_pdf_path, "filename", ""):
        extracted_text, _ = pdf_service.extract_text_from_pdf(uploaded_pdf_path)
        if not extracted_text.strip():
            raise ValueError("The uploaded PDF file is empty or could not be read.")
        uploaded_pdf_name = uploaded_pdf_path.filename

    final_content = extracted_text if extracted_text else content
    validation_helpers.validate_note_data(title, final_content)

    new_note = Note(
        user_id=user_id,
        topic_id=topic_id,
        title=title,
        content=final_content,
        uploaded_pdf_path=uploaded_pdf_name,
    )
    db.session.add(new_note)
    db.session.commit()
    return new_note

def view_note(note_id, user_id):
    """Return a note only after confirming it exists and belongs to the user."""
    note = db.session.get(Note, note_id)
    if not note:
        raise ValueError("Note not found!")
    if note.user_id != user_id:
        raise ValueError("You do not have permission to view this note!")
    return note

def delete_note(note_id, user_id):
    """Delete a note after verifying that the requesting user owns it."""
    note = Note.query.get(note_id)
    if not note:
        raise ValueError("Note not found!")
    if note.user_id != user_id:
        raise ValueError("You do not have permission to delete this note!")
    db.session.delete(note)
    db.session.commit()

def edit_note(note_id, user_id, title, content):
    """Validate and persist new title and content for an owned note."""
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