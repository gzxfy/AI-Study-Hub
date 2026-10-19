# AI Study Hub

**[▶ Watch the project demo · 2 min 35 sec](docs/studyhub-demo.mp4)**

[![Watch the AI Study Hub demo: notes, flashcards, study sessions, and the AI Assistant](docs/studyhub-demo-preview.jpg)](docs/studyhub-demo.mp4)

*Click the preview or the link above to open the demo video.*

A study workspace for organizing course notes, practicing recall with flashcards, and working through difficult concepts with an AI tutor.

## About

AI Study Hub is a full-stack Computer Science portfolio project built with React and Flask. It brings study material and revision tools into one workspace: organize notes by topic, create flashcards, review them in study sessions, and ask questions using saved notes as AI context.

The React frontend communicates with the existing Flask backend through HTTP endpoints. Flask handles authentication, ownership checks, database operations, and OpenAI requests. Notes and AI conversations are stored so students can return to their work later.

## Features

- **Accounts:** Register, sign in, and sign out using Flask session authentication and CSRF-protected requests.
- **Dashboard:** View saved material counts, recent notes, and recorded flashcard study progress.
- **Notes:** Create, read, edit, delete, and search notes by title or topic.
- **Topics:** Organize notes into subjects and manage topic names, descriptions, and colors.
- **Flashcards:** Create and edit question-and-answer cards, search the library, and filter cards by note, topic, or difficulty.
- **Study sessions:** Reveal answers, mark cards as correct or needing practice, and view a session summary.
- **AI Assistant:** Open a note's saved conversation, preview its content, ask follow-up questions, and optionally include related topic notes. Starter prompts help with summaries, explanations, and practice questions.
- **Responsive interface:** Shared navigation, keyboard shortcuts in the assistant, and visible loading, empty, and error states.

The backend also contains quiz, study-plan, and PDF-extraction services. These are separate from the current React workflows; the demo and feature list above describe the connected frontend.

## Technology

| Layer | Tools |
| --- | --- |
| Frontend | React, React Router, Vite, CSS |
| Backend | Python, Flask, Flask-SQLAlchemy, Flask-Migrate, Flask-WTF |
| Database | SQLAlchemy models; SQLite for local setup and tests, MySQL through PyMySQL for configured environments |
| AI | OpenAI Python SDK, called from Flask |
| Tests | Pytest and Node.js test runner |

## Architecture

```mermaid
flowchart TD
    React[React frontend] -->|HTTP requests and session cookies| Routes[Flask routes]
    Routes --> Services[Application services]
    Services --> Models[SQLAlchemy models]
    Models --> Database[(Database)]
    Services -->|Note context and conversation history| OpenAI[OpenAI API]
```

- Users own topics, notes, flashcards, and study records. The API checks ownership before accessing private material.
- Notes can belong to a topic, and flashcards are linked to notes.
- Conversations group saved user and assistant messages for a note.
- React calls Flask to ask AI questions. The OpenAI key stays on the server.
- A shared frontend API client sends session cookies and obtains a fresh CSRF token before mutations.

## Run locally

The default setup uses a persistent **SQLite database inside this checkout**. You do not need MySQL, a `.env` file, or an OpenAI key to try notes, topics, flashcards, and study sessions. Real AI replies require your own OpenAI key.

Requirements: Git, Python (tested with 3.14), and Node.js 22.12 or newer.

### 1. Get the project

Clone into a new folder beside your other projects, not inside another copy of this repository:

```bash
git clone https://github.com/gzxfy/AI-Study-Hub.git
cd AI-Study-Hub
```

### 2. Install Python dependencies

On Windows PowerShell, from the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

On macOS/Linux:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

These commands use the project's Python directly; activating the virtual environment is optional.

### 3. Start the backend

On Windows PowerShell, from the repository root:

```powershell
.\.venv\Scripts\python.exe run_local.py
```

On macOS/Linux:

```bash
.venv/bin/python run_local.py
```

The local launcher:

1. Selects `instance/studyhub-local.db`, separate from any configured MySQL database.
2. Saves a stable local session key in `instance/local-secret-key`.
3. Applies the committed Alembic migrations and stops if they fail.
4. Starts Flask at **http://127.0.0.1:5000**.

**Keep this terminal running.** Local mode deliberately skips `.env` and overrides `DATABASE_URL`, so a copied configuration or example MySQL credentials cannot break first-run setup. Saved local data remains available after restarting the launcher. Keep `instance/` local, including its database and session key.

To check the database setup without starting a server, add `--check`:

```powershell
.\.venv\Scripts\python.exe run_local.py --check
```

The migration head is `d8a17c09e452`. The configured migration directory is `alembic/`; see [migration notes](alembic/README). Do not run `db init`, `db stamp head`, or `db.create_all()` to bypass an upgrade failure.

### 4. Start the frontend in a second terminal

Open a **second terminal at the repository root**:

```bash
cd frontend
npm ci
npm run dev
```

Open **http://127.0.0.1:5173/app**, register an account, then create a topic and note. Both servers must remain running. Vite forwards `/api` and `/study_mode` requests to Flask on port 5000.

`npm run dev` stays running until Ctrl+C. You do not run the production build afterward in that same terminal to start the app.

### Optional: enable real AI replies

Set your own valid `OPENAI_API_KEY` in the **backend terminal** before launching local mode. In PowerShell:

```powershell
$env:OPENAI_API_KEY = 'your-real-openai-api-key'
.\.venv\Scripts\python.exe run_local.py
```

On macOS/Linux:

```bash
export OPENAI_API_KEY='your-real-openai-api-key'
.venv/bin/python run_local.py
```

Replace the example value with your own key. OpenAI requests can incur usage charges. The key stays on the backend; never put it in React or commit it. Local mode does not read a key from `.env`.

### Optional: use your own MySQL database

Use the standard Flask entry point instead of `run_local.py` when you want your own database configuration. It reads `.env` or environment variables. You must create the database and use an existing MySQL account with access to it; the local launcher does not create MySQL users or databases.

Example configuration (replace the account, password, and database with real local values):

```dotenv
SECRET_KEY=replace-with-a-long-random-secret
DATABASE_URL=mysql+pymysql://YOUR_MYSQL_USER:YOUR_MYSQL_PASSWORD@localhost:3306/YOUR_DATABASE
OPENAI_API_KEY=your-real-openai-api-key
```

Do not copy these placeholders unchanged. URL-encode special characters in the database username/password. Use a separate empty database for a fresh-install test.

With the project's virtual environment activated, run:

```powershell
python -m flask --app run.py db upgrade
if ($LASTEXITCODE -ne 0) { throw "Database migration failed. Fix it before starting Flask." }
python -m flask --app run.py db current
```

Only after the upgrade succeeds:

```bash
python run.py
```

Live MySQL migration verification requires your own working MySQL account. The automated migration tests use SQLite and do not prove a MySQL installation is configured correctly.

### Optional: check the production build

Open a **third terminal at the repository root**:

```bash
npm --prefix frontend run build
```

This creates `frontend/dist/` and exits; it does not start either server. A production host must serve the compiled frontend, handle React route refreshes, and forward backend requests. The local launcher and Vite development proxy are for local development.

### Update an existing clean-test checkout

Stop both servers first. From the root of that checkout:

```powershell
git status --short
git pull --ff-only
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe run_local.py
```

Check `git status` for local work before pulling. Start React in a second terminal using step 4. The local database and session key remain in that checkout's `instance/` directory; an old MySQL `.env` does not affect local mode.

Make sure fixes are committed and pushed from the original project before pulling them here. Check that `run_local.py` exists in the updated checkout. Keep test clones beside the original project, and never commit a nested checkout into the parent repository.

### Troubleshooting

| Symptom | What it means / next step |
| --- | --- |
| MySQL `1045: Access denied for user 'username'` | The standard Flask entry point is using example credentials. Use `run_local.py` for the SQLite quick start, or supply a real MySQL account. Reinstalling dependencies will not fix account credentials. |
| Missing `alembic/env.py` or `run_local.py` | Check the current branch and pull the commit containing the setup files. A pull cannot retrieve an unpushed local commit. |
| `No module named flask` | Install requirements using the same `.venv` Python used to launch the app. |
| Port 5000 or 5173 already in use | Stop the other project's development server before starting this checkout. If only 5173 is busy, use `npm run dev -- --port 5174` and open the URL printed by Vite; the backend stays on 5000. |
| Frontend cannot reach the API | Keep the Flask terminal running and read its error. Start Vite with `npm run dev`, which supplies the local API proxy. |
| Migration fails on a conflicting existing SQLite table | Stop and investigate that checkout's local schema. For an isolated new test, use `run_local.py --data-dir instance/fresh-test`; do not delete your normal database or stamp over the failure. |
| AI cannot answer | Local notes/study tools work without AI. Real replies require a valid backend API key and provider access. |

## Tests

Run the backend suite from the repository root with the Python virtual environment active:

```bash
python -m pytest
```

Latest verified backend result, including the four migration regression tests:

```text
171 passed, 1 skipped, 731 warnings in 19.94s
```

This result does not mean the application has zero warnings or that every deployment workflow has been tested. Review the skipped test and warnings when preparing a release.

Run the frontend tests and production build from the repository root:

```bash
npm --prefix frontend test
npm --prefix frontend run build
```

Frontend assistant tests cover conversation response validation, request IDs for retries, message formatting, session credentials, CSRF, cancellation, and request failures. Backend migration tests build the schema through Alembic instead of `db.create_all()`, verify model columns, exercise the signed-in study flow, and check that upgrades preserve existing data. Local-launcher tests verify that placeholder MySQL settings are overridden, data/session keys survive restarts, and migration failures stop startup. Pytest is configured to discover `test/`, so a nested test checkout is not accidentally collected as a second test suite.

The local setup was also checked with a new virtual environment, a fresh `pip install -r requirements.txt`, and `npm ci`. Both servers were started, and real HTTP requests through Vite verified registration, login, note/topic creation, note editing, flashcard reviews, study summaries, progress, conversation history, and logout. Browser login and the populated dashboard were verified as well. The verification used isolated local data; it did not use an existing MySQL database or make paid OpenAI calls.

## Project layout

```text
backend/
  models/       SQLAlchemy entities and relationships
  routes/       Flask HTTP endpoints
  services/     Application and AI logic
  utils/        Shared validation
frontend/
  src/
    api/        Requests to Flask
    assistant/  Conversation UI and response formatting
    auth/       Session state and protected routes
    components/ Shared UI components
    hooks/      Data loading helpers
    layouts/    Shared page layouts
    pages/      Application screens
    styles/     CSS
  tests/        Frontend tests
alembic/        Currently configured migration directory
docs/           Demo video and preview image
test/           Backend tests
templates/      Legacy Jinja templates
static/         Legacy Flask assets
run.py          Flask entry point
run_local.py    Migrate and start an isolated local SQLite workspace
```

## Next steps
- Change the database to PostgreSQL
- Update the backend to Django
- Verify migration upgrades against the deployment MySQL database and complete production hosting setup.
- Expand browser testing across the main workflows and mobile layouts.
- Improve AI availability errors, usage limits, and handling of concurrent requests.
- Continue backend cleanup after verifying the connected frontend workflows.


