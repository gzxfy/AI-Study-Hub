import os

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

def ask_ai(question, note_content, conversation_messages):
    messages=[
        {"role": "assistant", 
        "content": (
            "You are an AI study assistant. "
            "Use the provided note content as the primary source of information. "
            "If the answer is not in the note, clearly state that and provide general help."
            )
        },
        {
            "role": "assistant",
            "content": f"Note content:\n{note_content}"
        }
    ]
    # previous conversation messages
    for msg in conversation_messages:
        messages.append(
            {
                "role": msg.role,
                "content": msg.content
            }
        )

    # current user question
    messages.append(
        {
            "role": "user",
            "content": question
        }
    )

    client = _build_client()
    if client is None:
        return f"AI service is unavailable. Question received: {question}"

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

def generate_study_plan_with_AI(user_id, learning_context):
    """
    Generates a personalized study plan for the user based on their learning context.

    Args:
        user_id (int): The ID of the user.
        learning_context (dict): A dictionary containing the user's notes, study events, and quizzes.
    """
    notes = learning_context.get("notes", [])
    study_events = learning_context.get("study_events", [])
    quizzes = learning_context.get("quizzes", [])

    # Prepare the prompt for the AI model
    prompt = (
        "You are an AI study planner. Based on the user's learning context, "
        "create a personalized study plan that includes recommendations for reviewing notes, "
        "attending study events, and preparing for quizzes. "
        "Provide a structured plan with specific actions and timelines.\n\n"
        f"Notes: {[note.title for note in notes]}\n"
        f"Study Events: {[event.title for event in study_events]}\n"
        f"Quizzes: {[quiz.title for quiz in quizzes]}"
    )

    client = _build_client()
    if client is None:
        return "AI service is unavailable. Unable to generate a study plan."

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are concise, supportive, and specific in your feedback to help the learner understand their quiz question performance."},
            {"role": "user", "content": prompt}
        ]
    )
    
    return response.choices[0].message.content