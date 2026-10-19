import os
from types import SimpleNamespace

import pytest

from backend.models.models import Message
from backend.services import ai_service


def test_mode_detection():
    assert ai_service.detect_mode_from_question("Quiz the concept of gravity.") == "quiz"
    assert ai_service.detect_mode_from_question("What is the capital of France?") == "question"
    assert ai_service.detect_mode_from_question("Summarize the article about climate change.") == "summary"
    assert ai_service.detect_mode_from_question("This is a random statement.") == "general"


def test_build_messages_includes_relevant_note_context_and_history():
    question = "How does photosynthesis use light energy?"
    note_content = (
        "Photosynthesis uses light energy to convert carbon dioxide and water "
        "into glucose and oxygen."
    )
    history = [
        Message(role="user", content="What is photosynthesis?"),
        Message(role="assistant", content="It is how plants make sugars using light."),
    ]

    messages = ai_service.build_messages(question, note_content, history)

    assert messages[0]["role"] == "system"
    assert "study tutor" in messages[0]["content"].lower()
    assert note_content in messages[1]["content"]
    assert messages[2:4] == [
        {"role": "user", "content": "What is photosynthesis?"},
        {"role": "assistant", "content": "It is how plants make sugars using light."},
    ]
    assert messages[-1] == {"role": "user", "content": question}


def test_build_messages_maps_general_questions_to_teaching_instruction():
    messages = ai_service.build_messages(
        "This is a general question.",
        "The note explains the topic.",
        conversation_messages=[],
    )

    assert "check-for-understanding question" in messages[0]["content"]


def test_build_messages_does_not_duplicate_current_question():
    question = "What is AI?"
    messages = ai_service.build_messages(
        question,
        "AI stands for artificial intelligence.",
        [Message(role="user", content="Hello"), Message(role="assistant", content="Hi!")],
    )

    current_question_count = sum(
        message == {"role": "user", "content": question}
        for message in messages
    )
    assert current_question_count == 1


def test_ask_ai_sends_built_context_to_client(monkeypatch):
    captured = {}

    def create_completion(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="A deterministic tutor reply."))]
        )

    fake_client = SimpleNamespace(
        chat=SimpleNamespace(
            completions=SimpleNamespace(create=create_completion),
        ),
    )
    monkeypatch.setattr(ai_service, "_build_client", lambda: fake_client)
    history = [Message(role="user", content="Earlier question")]

    response = ai_service.ask_ai(
        "Explain the key idea.",
        "The note's key idea is conservation of energy.",
        history,
    )

    assert response == "A deterministic tutor reply."
    assert captured["model"] == "gpt-4o-mini"
    assert "conservation of energy" in captured["messages"][1]["content"]
    assert captured["messages"][2] == {"role": "user", "content": "Earlier question"}
    assert captured["messages"][-1] == {"role": "user", "content": "Explain the key idea."}


def test_ask_ai_returns_clear_fallback_without_client(monkeypatch):
    monkeypatch.setattr(ai_service, "_build_client", lambda: None)

    response = ai_service.ask_ai("hello", "A note.", conversation_messages=[])

    assert response.startswith("AI service is not available.")


@pytest.mark.integration
@pytest.mark.skipif(
    os.getenv("RUN_AI_INTEGRATION") != "1",
    reason="Set RUN_AI_INTEGRATION=1 to make a live OpenAI request.",
)
def test_live_ai_provider_returns_text():
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY is required for the live AI integration test.")

    response = ai_service.ask_ai(
        "Reply with one short greeting.",
        "The learner is testing their study assistant.",
        conversation_messages=[],
    )

    assert isinstance(response, str)
    assert response.strip()