from io import BytesIO

from backend import db
from backend.models.models import Note, User
from backend.services import note_service


def create_signed_in_user(client, test_app):
    with test_app.app_context():
        user = User(
            username="pdf-learner",
            email="pdf-learner@example.com",
            password_hash="not-used-by-these-tests",
        )
        db.session.add(user)
        db.session.commit()
        user_id = user.id

    with client.session_transaction() as session:
        session["user_id"] = user_id
    return user_id


def test_pdf_upload_creates_note_from_extracted_text(
    client, test_app, monkeypatch
):
    user_id = create_signed_in_user(client, test_app)
    monkeypatch.setattr(
        note_service.pdf_service,
        "extract_text_from_pdf",
        lambda uploaded_file: ("Extracted PDF text", 1),
    )

    response = client.post(
        "/api/notes/upload",
        data={
            "title": "PDF Note",
            "content": "Fallback text",
            "note_pdf": (BytesIO(b"fake PDF bytes"), "note.pdf"),
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 201
    assert response.json["note"]["title"] == "PDF Note"
    assert response.json["note"]["content"] == "Extracted PDF text"
    with test_app.app_context():
        note = Note.query.filter_by(user_id=user_id, title="PDF Note").one()
        assert note.content == "Extracted PDF text"
        assert note.uploaded_pdf_path == "note.pdf"


def test_empty_pdf_upload_returns_validation_error(client, monkeypatch):
    create_signed_in_user(client, client.application)
    monkeypatch.setattr(
        note_service.pdf_service,
        "extract_text_from_pdf",
        lambda uploaded_file: ("", 0),
    )

    response = client.post(
        "/api/notes/upload",
        data={
            "title": "Empty PDF Note",
            "content": "Fallback text",
            "note_pdf": (BytesIO(b"fake PDF bytes"), "empty.pdf"),
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 400
    assert response.json["error"] == {
        "code": "validation_error",
        "message": "The uploaded PDF file is empty or could not be read.",
    }