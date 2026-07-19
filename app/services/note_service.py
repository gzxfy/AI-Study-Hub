from app import db
from app.models.models import Note, db
import app.utils.validation_helpers as validation_helpers
import app.services.pdf_service as pdf_service

def create_note(user_id, title, content, topic_id, uploaded_pdf_path=None):
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