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
| Database | SQLAlchemy models; MySQL through PyMySQL, SQLite for isolated tests |
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

### 1. Install backend dependencies

Requirements: Python, a database, and Node.js 22.12+ for the frontend.

From the repository root, on Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

On macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

### 2. Configure Flask

Create a `.env` file in the repository root with your local values:

```dotenv
SECRET_KEY=replace-with-a-long-random-secret
DATABASE_URL=mysql+pymysql://username:password@localhost:3306/studyhub
OPENAI_API_KEY=your-openai-api-key
```

Create an empty MySQL database first and replace the example credentials. For a clean installation, use a separate database such as `studyhub_clean_test`; do not point the test checkout at your normal database. Keep real credentials out of source control. Use a stable `SECRET_KEY` and a persistent `DATABASE_URL`; the fallback in-memory database does not preserve data between runs. The AI Assistant requires a working OpenAI configuration.

For a quick local setup without installing MySQL, use this database setting instead:

```dotenv
DATABASE_URL=sqlite:///studyhub.db
```

Flask stores that SQLite file in its `instance/` directory. Do not copy an existing database into a fresh-install test.

From the repository root, with the virtual environment active, apply the committed migrations. On PowerShell:

```powershell
python -m flask --app run.py db upgrade
if ($LASTEXITCODE -ne 0) { throw "Database migration failed. Fix it before starting Flask." }
python -m flask --app run.py db current
```

On macOS/Linux, run `python -m flask --app run.py db upgrade`, check that it succeeds, then run `python -m flask --app run.py db current`.

The current migration head is `d8a17c09e452`. The configured migration directory is `alembic/`; all of its setup files and revisions must be included in the clone. Do not run `db init`, `db stamp head`, or `db.create_all()` to bypass a failed upgrade. See [migration notes](alembic/README).

**Only after the upgrade succeeds**, start Flask in this terminal:

```bash
python run.py
```

Flask runs at `http://127.0.0.1:5000`. Keep this terminal running. Starting Flask alone does not create or migrate the database. Automated migration tests exercise a fresh SQLite database and upgrades with saved rows; a live MySQL migration remains an environment-specific verification step.

### 3. Start React

Open a **second terminal** in the repository root and install frontend dependencies:

```bash
cd frontend
npm ci
```

Then start the development server from `frontend/`:

```bash
npm run dev
```

Open **http://127.0.0.1:5173/app**. Keep both terminals running: Flask serves the backend and Vite forwards `/api` and `/study_mode` requests to it. Use a private browser window and register a new account when testing a clean installation.

### Optional: check the production build

`npm run dev` stays running until you stop it with Ctrl+C. You do not need to run a build to use the development app. To verify that production assets compile, open a **third terminal at the repository root** and run:

```bash
npm --prefix frontend run build
```

This creates `frontend/dist/` and exits. It does not launch either server. A production host must serve the compiled frontend, handle React route refreshes, and forward backend requests. Vite's development proxy does not configure production hosting.

### Reuse a clean-test checkout

A second clone is a separate working copy. Fix and commit code in your main project, push the commit, then pull it into the test checkout. If you created `AI-Study-Hub-clean-test` inside the main project, run these commands **from that test folder**, after stopping its servers:

```powershell
git status --short
git pull --ff-only
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m flask --app run.py db upgrade
if ($LASTEXITCODE -ne 0) { throw "Database migration failed. Fix it before starting Flask." }
python run.py
```

Check `git status` for local edits before pulling. In the test checkout's second terminal, run `npm ci` from `frontend/` and then `npm run dev`. Keep its own `.env`, virtual environment, and separate database local. The first failed upgrade can be retried after pulling the fix; if it created partial tables, use a new empty test database rather than deleting your main database.

For future clean-install checks, create the clone **beside** the original project instead of inside it. The test checkout does not belong in the original project's commit. You can keep it for future tests, or remove it later after stopping its servers and checking that it contains no work you need.

## Tests

Run the backend suite from the repository root with the Python virtual environment active:

```bash
python -m pytest
```

Latest verified backend result, including the four migration regression tests:

```text
169 passed, 1 skipped, 731 warnings in 10.42s
```

This result does not mean the application has zero warnings or that every deployment workflow has been tested. Review the skipped test and warnings when preparing a release.

Run the frontend tests and production build from the repository root:

```bash
npm --prefix frontend test
npm --prefix frontend run build
```

Frontend assistant tests cover conversation response validation, request IDs for retries, message formatting, session credentials, CSRF, cancellation, and request failures. Backend migration tests build the schema through Alembic instead of `db.create_all()`, verify model columns, exercise the signed-in study flow, and check that upgrades preserve existing data. Pytest is configured to discover `test/`, so a nested test checkout is not accidentally collected as a second test suite.

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
```

## Next steps
- Change the database to PostgreSQL
- Update the backend to Django
- Verify migration upgrades against the deployment MySQL database and complete production hosting setup.
- Expand browser testing across the main workflows and mobile layouts.
- Improve AI availability errors, usage limits, and handling of concurrent requests.
- Continue backend cleanup after verifying the connected frontend workflows.


