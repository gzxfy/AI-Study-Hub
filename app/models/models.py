from datetime import datetime
from flask_login import UserMixin
from .. import db

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    topics = db.relationship('Topic', backref='user', cascade="all, delete-orphan")
    notes = db.relationship('Note', backref='user', cascade="all, delete-orphan")
    conversations = db.relationship('Conversation', backref='user', cascade="all, delete-orphan")
    progress = db.relationship('Progress', backref='user', cascade="all, delete-orphan")
    flashcards = db.relationship('Flashcard', backref='user', cascade="all, delete-orphan")

    def __repr__(self):
        return f'<User {self.username}>'
    
class Topic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    color = db.Column(db.String(7), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    notes = db.relationship('Note', backref='topic', cascade="all, delete-orphan")
    progress = db.relationship('Progress', backref='topic', cascade="all, delete-orphan")
    flashcards = db.relationship('Flashcard', backref='topic', cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Topic {self.title}>'
    
class Note(db.Model):
    __tablename__ = 'notes'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    topic_id = db.Column(db.Integer, db.ForeignKey('topic.id'), nullable=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    conversation = db.relationship('Conversation', backref='note', cascade='all, delete-orphan', uselist=False)
    flashcards = db.relationship('Flashcard', backref='note', cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Note {self.title}>'
    
class Conversation(db.Model):
    __tablename__ = 'conversations'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    note_id = db.Column(db.Integer, db.ForeignKey('notes.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    messages = db.relationship('Message', backref='conversation', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Conversation {self.id} for Note {self.note_id}>'
    
class Message(db.Model):
    __tablename__ = 'messages'

    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversations.id'), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'user' or 'assistant'
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


    def __repr__(self):
        return f'<Message {self.role} in Conversation {self.conversation_id}>'
    
class Progress(db.Model):
    __tablename__ = 'progress'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    topic_id = db.Column(db.Integer, db.ForeignKey('topic.id'), nullable=False)
    notes_count = db.Column(db.Integer, default=0)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Progress {self.notes_count} notes for Topic {self.topic_id}>'
    
class Flashcard(db.Model):
    __tablename__ = 'flashcards'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    topic_id = db.Column(db.Integer, db.ForeignKey('topic.id'), nullable=True)
    note_id = db.Column(db.Integer, db.ForeignKey('notes.id'), nullable=False)
    question = db.Column(db.Text, nullable=False)
    answer = db.Column(db.Text, nullable=False)
    difficulty = db.Column(db.String(50), nullable=True)  # e.g., 'easy', 'medium', 'hard'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Flashcard {self.question[:20]}... Difficulty: {self.difficulty}>'
    
class FlashcardProgress(db.Model):
    __tablename__ = 'flashcard_progress'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    flashcard_id = db.Column(db.Integer, db.ForeignKey('flashcards.id'), nullable=False)
    times_seen = db.Column(db.Integer, default=0)  # e.g., number of times the flashcard has been seen
    times_correct = db.Column(db.Integer, default=0)  # e.g., number of times the flashcard has been answered correctly
    streak = db.Column(db.Integer, default=0)  # e.g., number of consecutive correct answers
    progress = db.Column(db.Integer, default=0)  # e.g., 0 to 100 representing progress percentage
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)  # e.g., timestamp of the last time the flashcard was seen
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<FlashcardProgress {self.progress}% for Flashcard {self.flashcard_id}>'
    
class QuizAttempt(db.Model):
    __tablename__ = 'quiz_attempts'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    topic_id = db.Column(db.Integer, db.ForeignKey('topic.id'), nullable=True)
    note_id = db.Column(db.Integer, db.ForeignKey('notes.id'), nullable=False)

    score = db.Column(db.Float, default=0)  
    status = db.Column(db.String(20), default='in_progress')  # 'in_progress', 'completed'
    question_index = db.Column(db.Integer, default=0)  # To track which question the user is currently on
    question_order = db.Column(db.Json, nullable=True)  # To store the order of flashcard IDs for the quiz attempt

    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    finished_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    question_attempts = db.relationship('QuizQuestionAttempt', backref='quiz_attempt', cascade='all, delete-orphan')
    def __repr__(self):
        return f'<QuizAttempt {self.id} for Note {self.note_id} Topic {self.topic_id} Score: {self.score}>'
    
class QuizQuestionAttempt(db.Model):
    __tablename__ = 'quiz_question_attempts'

    id = db.Column(db.Integer, primary_key=True)
    quiz_attempt_id = db.Column(db.Integer, db.ForeignKey('quiz_attempts.id'), nullable=False)
    flashcard_id = db.Column(db.Integer, db.ForeignKey('flashcards.id'), nullable=False)

    user_answer = db.Column(db.Text, nullable=False)
    correct_answer = db.Column(db.Text, nullable=False)
    is_correct = db.Column(db.Boolean, default=False)

    time_taken = db.Column(db.Float, default=0)  # Time taken to answer the question in seconds
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<QuizQuestionAttempt {self.id} for QuizAttempt {self.quiz_attempt_id} Flashcard {self.flashcard_id}>'