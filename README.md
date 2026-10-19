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

Create the database first and replace the example credentials. Keep real credentials out of source control. Use a stable `SECRET_KEY` and a persistent `DATABASE_URL`; the fallback in-memory database does not preserve data between runs. The AI Assistant requires a working OpenAI configuration.

Apply migrations and start Flask:

```bash
flask --app run.py db upgrade
python run.py
```

Flask runs at `http://127.0.0.1:5000`. The application config selects the migration directory `alembic/`. Fresh-database migration setup remains a release check; the automated tests create an isolated schema directly and do not prove migration readiness. SQLite migrations are not currently verified as a supported local setup.

### 3. Start React

In a second terminal:

```bash
cd frontend
npm ci
npm run dev
```

Open **http://127.0.0.1:5173/app**. Keep Flask running: Vite forwards `/api` and `/study_mode` requests to the backend.

Build the frontend with:

```bash
npm run build
```

A production host must serve the compiled frontend, handle React route refreshes, and forward backend requests. Vite's development proxy does not configure production hosting.

## Tests

Run the backend suite from the repository root with the Python virtual environment active:

```bash
pytest
```

Latest reported backend result:

```text
165 passed, 1 skipped, 715 warnings in 8.98s
```

This result does not mean the application has zero warnings or that every deployment workflow has been tested. Review the skipped test and warnings when preparing a release.

Run the frontend tests and production build from the repository root:

```bash
npm --prefix frontend test
npm --prefix frontend run build
```

Frontend assistant tests cover conversation response validation, request IDs for retries, message formatting, session credentials, CSRF, cancellation, and request failures.

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
- Verify a reproducible fresh-database installation and production deployment.
- Expand browser testing across the main workflows and mobile layouts.
- Improve AI availability errors, usage limits, and handling of concurrent requests.
- Continue backend cleanup after verifying the connected frontend workflows.


