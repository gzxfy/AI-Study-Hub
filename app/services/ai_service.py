from openai import OpenAI
import os
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages
    )
    
    return response.choices[0].message.content