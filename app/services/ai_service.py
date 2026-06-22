from openai import OpenAI
import os
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
def ask_ai(question, note_content):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": question}
        ]
    )
    print(response)
    print(response.choices[0].message.content)
    print(type(response))
    return response.choices[0].message.content
    print(type(response.choices[0].message.content))