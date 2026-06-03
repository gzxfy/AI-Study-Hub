import os
import secrets

from dotenv import load_dotenv

load_dotenv()

class Config:
    # Use env-provided key in deployed environments; generate a strong ephemeral key for local dev.
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(32)

    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///:memory:')
    if not SQLALCHEMY_DATABASE_URI:
        raise RuntimeError('DATABASE_URL environment variable is required')

    SQLALCHEMY_TRACK_MODIFICATIONS = False