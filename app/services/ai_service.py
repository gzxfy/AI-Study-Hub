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
    # This function can be expanded to use AI for analyzing feedback and providing insights
    # For now, it simply logs the feedback for the question attempt
    pass