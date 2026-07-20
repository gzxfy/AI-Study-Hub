import os
import json
from app.models.models import StudyPlan


try:
    from openai import OpenAI
except ModuleNotFoundError:
    OpenAI = None


def _build_client():
    if OpenAI is None:
        return None

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None

    return OpenAI(api_key=api_key)

# Helper function to build the system instruction for the AI model based on the mode of interaction (e.g., "quiz", "summary", or default tutoring mode).
def build_tutor_instruction(mode: str) -> str:
    base = (
        "You are a study tutor.\n"
        "Use provided note context as the primary source.\n"
        "If context is missing, say that clearly.\n"
        "Be concise and supportive."
    )

    if mode == "quiz":
        return base + (
            "\nReturn exactly one practice question."
            "\nDo not include the answer unless asked."
        )
    if mode == "summary":
        return base + (
            "\nGive a short summary and 3 key takeaways."
        )
    
    return base + (
         "\nExplain clearly, then ask one quick check-for-understanding question."
    )

def detect_mode_from_question(question: str) -> str:
    q = (question or "").strip().lower()

    # Quiz intent
    if (
        q.startswith("quiz:")
        or q.startswith("quiz me")
        or q.startswith("quiz ")
        or q.startswith("test me")
    ):
        return "quiz"

    # Summary intent
    if (
        q.startswith("summary:")
        or q.startswith("summarize")
        or q.startswith("summary ")
    ):
        return "summary"

    # Direct question vs general statement
    if q.endswith("?") or q.startswith(("what", "why", "how", "when", "where", "who")):
        return "question"

    return "general"

# Helper function to split text into chunks for processing by the AI model.
def chunk_text(text: str, size: int = 1200, overlap: int = 200) -> list[str]:
    """
    Splits the input text into chunks of a specified size with a specified overlap.

    :param text: The input text to be chunked.
    :param size: The maximum size of each chunk.
    :param overlap: The number of characters to overlap between chunks.
    :return: A list of text chunks.
    """
    chunks = []
    i = 0
    while i < len(text):
        chunks.append(text[i:i + size])
        i += size - overlap
    return chunks

# Helper function to select the most relevant chunks of note content based on the user's question.
def select_relevant_chunks(question: str, note_content: str, top_k: int = 3) -> list[str]:
    """
    Selects the most relevant chunks of note content based on the user's question.

    :param question: The user's current question.
    :param note_content: The full content of the note.
    :param top_k: The number of top relevant chunks to return.
    :return: A list of the most relevant text chunks.
    """
    terms = set((question or "").lower().split())
    scored = []
    for chunk in chunk_text(note_content or ""):
        score = len(terms.intersection(set(chunk.lower().split())))
        scored.append((score, chunk))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [c for s, c in scored[:top_k] if c.strip()]

# Helper function to build the message payload for the AI model, including system instructions, note content, previous conversation messages, and the current user question.
def build_messages(question, note_content, conversation_messages):
    mode = detect_mode_from_question(question)

    instruction_mode = mode if mode in ["quiz", "summary"] else "teach"

    selected = select_relevant_chunks(question, note_content, top_k=3)
    context_block = "\n\n".join(
        f"Context {idx+1}:\n{chunk}" for idx, chunk in enumerate(selected)
    ) or "No extractable note context provided."

    messages = [
        {"role": "system", "content": build_tutor_instruction(instruction_mode)},
        {"role": "system", "content": f"Study note context:\n{context_block}"},
    ]

    for msg in conversation_messages:
        messages.append({"role": msg.role, "content": msg.content})

    messages.append({"role": "user", "content": question})
    return messages


def ask_ai(question, note_content, conversation_messages):
    messages = build_messages(question, note_content, conversation_messages)
    client = _build_client()

    if client is None:
        return "AI service is not available. Please check your API key and dependencies."

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages
    )
    
    return response.choices[0].message.content

def review_quiz_question_with_AI(user_id, quiz_attempt_id, flashcard_id, feedback):
    from app.models.models import Flashcard, QuizAttempt, QuizQuestionAttempt
    quiz_attempt = QuizAttempt.query.filter_by(id=quiz_attempt_id, user_id=user_id).first()
    if not quiz_attempt:
        raise ValueError("Quiz attempt not found")
    
    flashcard = Flashcard.query.filter_by(id=flashcard_id, user_id=user_id).first()
    if not flashcard:
        raise ValueError("Flashcard not found")
    
    question_attempt = QuizQuestionAttempt.query.filter_by(quiz_attempt_id=quiz_attempt_id, flashcard_id=flashcard_id).first()
    if not question_attempt:
        raise ValueError("Quiz question attempt not found")
    
    correctness = "correct" if question_attempt.is_correct else "incorrect"
    prompt = (
        "You are a quiz review tutor. Explain clearly why the learner answer is right or wrong. "
        "Give one key concept and one improvement tip.\n\n"
        f"Question: {flashcard.question}\n"
        f"Correct answer: {question_attempt.correct_answer}\n"
        f"Learner answer: {question_attempt.user_answer}\n"
        f"Result: {correctness}\n"
        f"Learner context: {feedback or 'None'}"
    )
    client = _build_client()
    if client is None:
        if question_attempt.is_correct:
            return "Correct answer. Reinforce this concept with one more similar problem."
        return "Incorrect answer. Compare your answer with the correct one and focus on the key concept tested."
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are concise, supportive, and specific in your feedback to help the learner understand their quiz question performance."},
            {"role": "user", "content": prompt}
        ]
    )
    
    return response.choices[0].message.content

def generate_study_plan_with_AI(user_id, learning_context, days_until_exam=7):
    """Generates a personalized study plan for the user based on their learning context using AI.
    param user_id: The ID of the user for whom the study plan is being generated.
    param learning_context: A dictionary containing the user's learning context, including notes, flashcards, and quizzes.
    param days_until_exam: The number of days until the user's exam.
    return: A string containing the generated study plan.
    """
    notes = learning_context.get("notes", [])
    quizzes = learning_context.get("quizzes", [])
    flashcards = learning_context.get("flashcards", [])
    topics = learning_context.get("topics", [])

    notes_summary = "\n".join(
        f"- {n.title}: {(n.content or '')[:120]}"
        for n in notes[:20]
    ) or "No notes available."

    quizzes_summary = "\n".join(
        f"- Quiz {q.id}: score={q.score}, status={q.status}"
        for q in quizzes[:20]
    ) or "No quizzes available."

    flashcards_summary = "\n".join(
        f"- Q: {(f.question or '')[:80]} | difficulty={f.difficulty or 'unknown'}"
        for f in flashcards[:30]
    ) or "No flashcards available."

    topics_summary = ", ".join(topics) if topics else "No specific topics available."


    prompt = (
        f""" 
        You are an AI study planner.
        Create a {days_until_exam}-day study plan as valid JSON only.
        No markdown. No explanation text.

        Notes:
        {notes_summary}
        Flashcards:
        {flashcards_summary}
        Quizzes:
        {quizzes_summary}
        Topics:
        {topics_summary}

        return JSON with this shape:
        {{ 
            "title": "string",
            "days": [
                {{
                "day_number": 1,
                "focus": "string",
                "estimated_time_minutes": 60,
                "tasks": [
                    {{ "type": "note_review | flashcard_review | quiz | summary",
                    "description": "string" 
                    }}
                ],
            }},
        }}
        Rules:
        - Return exactly {days_until_exam} days
        - day_number must be 1 through {days_until_exam}
        - each day must have at least 2 tasks
        - last 2 days emphasize review and quiz practice
        """
    )

    client = _build_client()
    if client is None:
        return "AI service is not available. Please check your API key and dependencies."

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a strict JSON generator for study plans."},
            {"role": "user", "content": prompt}
        ]
    )

    raw_content = (response.choices[0].message.content or "").strip()
    try:
        plan_data = json.loads(raw_content)
    except json.JSONDecodeError:
        raise ValueError(f"AI returned invalid JSON for study plan.")
    
    days = plan_data.get("days", [])
    if len(days) != days_until_exam:
        raise ValueError(f"AI returned {len(days)} days, expected {days_until_exam}.")

    return plan_data