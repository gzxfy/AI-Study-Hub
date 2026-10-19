"""Verify the documented local launcher in a new Python process."""
import os
from pathlib import Path
import sqlite3
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


def check_local_setup(data_dir):
    environment = os.environ.copy()
    # Deliberately unusable custom settings must not affect an explicit local run.
    environment['DATABASE_URL'] = 'mysql+pymysql://username:password@127.0.0.1:1/not_a_database'
    environment['SECRET_KEY'] = 'not-the-local-session-key'
    result = subprocess.run(
        [sys.executable, str(ROOT / 'run_local.py'), '--check', '--data-dir', str(data_dir)],
        cwd=data_dir,
        env=environment,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, f'{result.stdout}\n{result.stderr}'
    assert 'Migration upgrade succeeded' in result.stdout


def test_local_launcher_ignores_placeholder_database_and_preserves_data(tmp_path):
    check_local_setup(tmp_path)
    key_file = tmp_path / 'local-secret-key'
    original_key = key_file.read_text(encoding='utf-8')
    assert len(original_key) == 64
    assert original_key != 'not-the-local-session-key'

    database = tmp_path / 'studyhub-local.db'
    with sqlite3.connect(database) as connection:
        assert connection.execute('SELECT version_num FROM alembic_version').fetchone() == ('d8a17c09e452',)
        connection.execute("INSERT INTO user (username, email, password_hash) VALUES ('persisted', 'persisted@example.com', 'test-only')")

    check_local_setup(tmp_path)
    assert key_file.read_text(encoding='utf-8') == original_key
    with sqlite3.connect(database) as connection:
        assert connection.execute('SELECT username FROM user').fetchall() == [('persisted',)]


def test_local_launcher_exits_if_migrations_fail(tmp_path):
    # A conflicting, unversioned table cannot be silently treated as migrated.
    with sqlite3.connect(tmp_path / 'studyhub-local.db') as connection:
        connection.execute('CREATE TABLE user (id INTEGER PRIMARY KEY)')
    environment = os.environ.copy()
    environment['STUDYHUB_LOCAL'] = '1'
    result = subprocess.run(
        [sys.executable, str(ROOT / 'run_local.py'), '--data-dir', str(tmp_path)],
        cwd=tmp_path,
        env=environment,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode != 0
    assert 'Backend: http://' not in result.stdout
