from sqlalchemy.exc import IntegrityError

from backend import db
from backend.models.models import Conversation, Message, Note
from backend.services.ai_service import ask_ai, ask_ai_with_topics


QUESTION_LIMIT = 2000


class NoteNotFoundError(ValueError):
    """Raised when a note does not exist or is not owned by the user."""


def _owned_note(note_id, user_id):
    note = Note.query.filter_by(id=note_id, user_id=user_id).first()
    if note is None:
        raise NoteNotFoundError("Note not found.")
    return note


def _get_or_create_conversation(note, user_id):
    conversation = Conversation.query.filter_by(
        note_id=note.id,
        user_id=user_id,
    ).first()
    if conversation is not None:
        return conversation

    conversation = Conversation(note_id=note.id, user_id=user_id)
    db.session.add(conversation)
    db.session.commit()
    return conversation


def _ordered_messages(conversation_id):
    return (
        Message.query
        .filter_by(conversation_id=conversation_id)
        .order_by(Message.timestamp.asc(), Message.id.asc())
        .all()
    )


def get_conversation_messages(note_id, user_id):
    """Return or initialize the conversation for an owned note."""
    note = _owned_note(note_id, user_id)
    conversation = _get_or_create_conversation(note, user_id)
    return _ordered_messages(conversation.id)


def send_message(note_id, user_id, question, include_topic=False, request_id=None):
    """Generate and persist one exchange, returning the updated history."""
    question = (question or "").strip()
    if not question:
        raise ValueError("Message cannot be empty.")
    if len(question) > QUESTION_LIMIT:
        raise ValueError(f"Message must be {QUESTION_LIMIT} characters or fewer.")

    note = _owned_note(note_id, user_id)
    conversation = _get_or_create_conversation(note, user_id)

    if request_id is not None:
        previous_message = Message.query.filter_by(
            conversation_id=conversation.id,
            role="user",
            request_id=request_id,
        ).first()
        if previous_message is not None:
            return _ordered_messages(conversation.id)

    prior_messages = _ordered_messages(conversation.id)
    if include_topic and note.topic_id is not None:
        topic_notes = (
            Note.query
            .filter_by(user_id=user_id, topic_id=note.topic_id)
            .order_by(Note.updated_at.desc(), Note.id.desc())
            .all()
        )
        answer = ask_ai_with_topics(
            user_id,
            question,
            topic_notes,
            prior_messages,
        )
    else:
        answer = ask_ai(question, note.content, prior_messages)

    if not isinstance(answer, str) or not answer.strip():
        raise RuntimeError("The assistant returned an empty response.")

    db.session.add_all([
        Message(
            conversation_id=conversation.id,
            role="user",
            content=question,
            request_id=request_id,
        ),
        Message(
            conversation_id=conversation.id,
            role="assistant",
            content=answer.strip(),
        ),
    ])
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        if request_id is not None:
            existing = Message.query.filter_by(
                conversation_id=conversation.id,
                role="user",
                request_id=request_id,
            ).first()
            if existing is not None:
                return _ordered_messages(conversation.id)
        raise
    except Exception:
        db.session.rollback()
        raise

    return _ordered_messages(conversation.id)