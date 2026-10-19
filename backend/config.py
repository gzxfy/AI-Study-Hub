import os
import secrets

from dotenv import load_dotenv

# The explicit local launcher uses its own SQLite database and secret. It must
# not inherit a .env copied from another checkout (or a placeholder MySQL URL).
if os.environ.get('STUDYHUB_LOCAL') != '1':
    load_dotenv()

class Config:
    # Use env-provided key in deployed environments; generate a strong ephemeral key for local dev.
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(32)

    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///:memory:')

    SQLALCHEMY_TRACK_MODIFICATIONS = False
