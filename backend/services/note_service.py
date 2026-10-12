from backend import db
from backend.models.models import (
    Conversation,
    Flashcard,
    FlashcardProgress,
    Message,
    Note,
    QuizAttempt,
    QuizQuestionAttempt,
    StudyEvent,
)
from backend.services import topic_service
import backend.utils.validation_helpers as validation_helpers
import backend.services.pdf_service as pdf_service


class InvalidTopicError(ValueError):
    """Raised when a note references a topic the user cannot access."""


class NoteNotFoundError(ValueError):
    """Raised when a note does not exist or is not owned by the user."""


def list_notes(user_id):
    """Return a user's notes, newest updates first."""
    return (
        Note.query
        .filter_by(user_id=user_id)
        .order_by(Note.updated_at.desc(), Note.id.desc())
        .all()
    )


def create_note(user_id, title, content, topic_id, uploaded_pdf_path=None):
    """Extract optional PDF text, validate it, and save a study note."""
    if topic_id is not None and not topic_service.topic_belongs_to_user(
        topic_id, user_id
    ):
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
        raise NoteNotFoundError("Note not found!")
    if note.user_id != user_id:
        raise NoteNotFoundError("You do not have permission to view this note!")
    return note


def update_note(note_id, user_id, title, content, topic_id):
    """Validate and persist an owned note, including its topic assignment."""
    note = db.session.get(Note, note_id)
    if not note:
        raise NoteNotFoundError("Note not found!")
    if note.user_id != user_id:
        raise NoteNotFoundError("You do not have permission to edit this note!")
    if topic_id is not None and not topic_service.topic_belongs_to_user(
        topic_id, user_id
    ):
        raise InvalidTopicError("Topic is invalid or unavailable.")

    validation_helpers.validate_note_data(title, content)
    note.title = title.strip()
    note.content = content
    note.topic_id = topic_id
    db.session.commit()
    return note


def delete_note(note_id, user_id):
    """Delete an owned note and its note/flashcard study records atomically."""
    note = db.session.get(Note, note_id)
    if not note:
        raise NoteNotFoundError("Note not found!")
    if note.user_id != user_id:
        raise NoteNotFoundError("You do not have permission to delete this note!")
    flashcard_ids = db.session.query(Flashcard.id).filter_by(note_id=note.id)
    quiz_attempt_ids = db.session.query(QuizAttempt.id).filter_by(note_id=note.id)
    conversation_ids = db.session.query(Conversation.id).filter_by(note_id=note.id)

    db.session.query(Message).filter(
        Message.conversation_id.in_(conversation_ids)
    ).delete(synchronize_session=False)
    db.session.query(Conversation).filter(
        Conversation.id.in_(conversation_ids)
    ).delete(synchronize_session=False)

    db.session.query(QuizQuestionAttempt).filter(
        (QuizQuestionAttempt.quiz_attempt_id.in_(quiz_attempt_ids))
        | (QuizQuestionAttempt.flashcard_id.in_(flashcard_ids))
    ).delete(synchronize_session=False)
    db.session.query(QuizAttempt).filter(
        QuizAttempt.id.in_(quiz_attempt_ids)
    ).delete(synchronize_session=False)

    db.session.query(StudyEvent).filter(
        StudyEvent.flashcard_id.in_(flashcard_ids)
    ).delete(synchronize_session=False)
    db.session.query(FlashcardProgress).filter(
        FlashcardProgress.flashcard_id.in_(flashcard_ids)
    ).delete(synchronize_session=False)
    db.session.query(Flashcard).filter(
        Flashcard.id.in_(flashcard_ids)
    ).delete(synchronize_session=False)

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