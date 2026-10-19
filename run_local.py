"""Start a local SQLite workspace after applying its database migrations.

Run with the project's virtual environment: python run_local.py
This launcher never reads .env and never connects to the configured MySQL DB.
"""
import argparse
import os
from pathlib import Path
import secrets


ROOT = Path(__file__).resolve().parent


def create_local_app(data_dir=None):
    """Use a persistent, separate database and session key for this checkout."""
    os.environ['STUDYHUB_LOCAL'] = '1'
    directory = Path(data_dir or ROOT / 'instance').resolve()
    directory.mkdir(parents=True, exist_ok=True)
    key_path = directory / 'local-secret-key'
    try:
        descriptor = os.open(key_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        key = key_path.read_text(encoding='utf-8').strip()
        if not key:
            raise RuntimeError('The local session key file is empty. Restore a valid key before starting.')
    else:
        key = secrets.token_hex(32)
        with os.fdopen(descriptor, 'w', encoding='utf-8') as file:
            file.write(key)

    # Import after setting local mode, before backend configuration is loaded.
    from backend import create_app

    database = directory / 'studyhub-local.db'
    return create_app({
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{database.as_posix()}',
        'SECRET_KEY': key,
    })


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Apply migrations and exit without starting a server.')
    parser.add_argument('--data-dir', type=Path, help='Use a separate directory for local data (default: instance/).')
    parser.add_argument('--port', type=int, default=5000, help='Local backend port (default: 5000).')
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error('--port must be between 1 and 65535')

    app = create_local_app(args.data_dir)
    from flask_migrate import upgrade

    # Failure here exits before app.run; no server starts with an unusable schema.
    with app.app_context():
        upgrade(directory=str(ROOT / 'alembic'))
    print('Local SQLite database is ready. Migration upgrade succeeded.', flush=True)
    if args.check:
        return
    print(f'Backend: http://127.0.0.1:{args.port}', flush=True)
    print('Start React in a second terminal: cd frontend, npm ci, npm run dev', flush=True)
    print('Local mode skips .env. To enable real AI, set OPENAI_API_KEY in this terminal.', flush=True)
    app.run(host='127.0.0.1', port=args.port, debug=False, use_reloader=False, load_dotenv=False)


if __name__ == '__main__':
    main()
