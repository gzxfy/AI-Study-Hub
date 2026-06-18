def ask_ai(question, note_content):
    # This is a placeholder function for interacting with an AI service
    # In a real implementation, this function would send the message to the AI and return the response
    prompt = f"""
    Note = 
    {note_content}
    Question = 
    {question}
    """
    return f'You said: {question} Note content: {note_content}'
