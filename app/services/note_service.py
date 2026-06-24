from app import db
from app.models.models import User, Conversation, note, Topic, db, Message

def create_note(user_id, conversation_id, topic_id, content):
    
    new_note = note(user_id=user_id, conversation_id=conversation_id, topic_id=topic_id, content=content)
    db.session.add(new_note)
    db.session.commit()
    return new_note