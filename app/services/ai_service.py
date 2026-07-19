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

def chunk_text(text, chunk_size=1000, overlap=200):
    """
    Splits the input text into chunks of specified size with optional overlap.
    
    :param text: The input text to be chunked.
    :param chunk_size: The maximum size of each chunk.
    :param overlap: The number of characters to overlap between chunks.
    :return: A list of text chunks.
    """
    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        
        # Move the start index forward by chunk_size - overlap to create overlap
        start += chunk_size - overlap
    
    return chunks

def select_relevant_chunks(question, note_content, top_k=3):
    """
    Selects the most relevant chunks of note content based on the question.
    
    :param question: The user's question.
    :param note_content: The full content of the note.
    :param top_k: The number of top relevant chunks to return.
    :return: A list of the most relevant text chunks.
    """
    # split the note content into chunks
    chunks = chunk_text(note_content)
    question_terms = set(question.lower().split())

    # Score each chunk based on the number of overlapping terms with the question
    scored=[]
    for chunk in chunks:
        chunk_terms = set(chunk.lower().split())
        # Calculate relevance score based on the number of overlapping terms
        score = len(question_terms & chunk_terms)
        scored.append((score, chunk))

    scored.sort(reverse=True, key=lambda item: item[0])  # Sort by score in descending order
    return [chunk for score, chunk in scored[:top_k] if chunk.strip()]  # Return only non-empty chunks

def build_messages(question, note_content, conversation_messages):
    """
    Constructs the message payload for the AI model, including system instructions,
    note content, previous conversation messages, and the current user question.
    
    :param question: The user's current question.
    :param note_content: The full content of the note.
    :param conversation_messages: List of previous messages in the conversation.
    :return: A list of messages formatted for the AI model.
    """

    relevant_chunks = select_relevant_chunks(question, note_content)
    context_block = "\n\n".join(
        f"Source chunk {index + 1}:\n{chunk}"
        for index, chunk in enumerate(relevant_chunks)
    )

    messages = [
        {
            "role": "system",
            "content": (
                "You are a study tutor.\n"
                "First answer using the note.\n"
                "Then summarize the key point in 1-2 bullets.\n"
                "Then ask one short practice question.\n"
                "If the note does not support the answer, say so clearly."
            )
        },
        {
            "role": "system",
            "content": f"Relevant note content:\n{context_block}"
        }
    ]

    # Add previous conversation messages
    for msg in conversation_messages:
        messages.append({
            "role": msg.role,
            "content": msg.content
        })

    # Add the current user question
    messages.append({
        "role": "user",
        "content": question
    })

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