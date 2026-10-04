# AI Study Hub

> A study workspace for organizing course material, practicing with flashcards and quizzes, and getting help from an AI tutor.

<!-- TODO: Replace this introduction with project summary and add project/demo links. -->

## About

AI Study Hub is a learning app built around a student's notes and topics. The Flask application provides account-based study tools, including notes, PDF text import, flashcards, study sessions, quizzes, progress tracking, and study plans. An optional OpenAI integration can answer questions using note content as context.

The repository currently has two user interfaces:

- The Flask/Jinja pages are the existing server-rendered application.
- The React/Vite app is an early layout preview at `/app`. It currently has navigation and placeholder feature pages, but does not authenticate users or call the Flask backend yet.

This distinction is intentional: the React screens should not be mistaken for live data or completed workflows. The existing Flask pages and JSON study endpoints are separate from that preview while frontend integration is in progress.

## Screenshots

<!-- TODO: Add screenshots to docs/screenshots/ and update these paths and captions. -->

<!-- | Screen | Preview |
| --- | --- |
| Home | `docs/screenshots/home.png` (add screenshot) |
| Notes and topics | `docs/screenshots/notes.png` (add screenshot) |
| Study or quiz flow | `docs/screenshots/study-session.png` (add screenshot) |
| React app preview | `docs/screenshots/react-preview.png` (add screenshot) |

To show an image here, replace a placeholder with Markdown such as `![Home page](docs/screenshots/home.png)` after adding the image file. -->

## Features

- Register and sign in with a user account.
- Create and organize topics, notes, and flashcards.
- Import text from PDF files into notes. (Will probably update it to use blob)
- Review flashcards and track study activity and progress.
- Take quizzes and review answers.
- Generate and track a study plan.
- Search notes and topics.
- Ask an AI tutor questions based on study-note context when `OPENAI_API_KEY` is configured.
- Preview the React application shell and its responsive navigation at `/app`.

Availability and completeness vary by interface. The Flask app contains the existing workflows; the React preview is not connected to them yet.

## Technology

- **Backend:** Python, Flask, Flask-SQLAlchemy, Flask-Migrate, Flask-Login, Flask-WTF  (Will most likely get changed to FastAPI)
- **Database:** SQLAlchemy-supported database; SQLite is convenient for local development
- **AI and documents:** OpenAI Python SDK (optional), pypdf
- **Frontend preview:** React, React Router, Vite
- **Tests:** pytest

## Run Locally

### Flask application

Requirements: Python and pip. From the repository root, create and activate a virtual environment, then install dependencies.

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Create a `.env` file in the repository root before running migrations:

```dotenv
SECRET_KEY=replace-this-with-a-long-random-value
DATABASE_URL=sqlite:///studyhub.db
# Optional: enables live OpenAI tutor responses
OPENAI_API_KEY=
```

`SECRET_KEY` should remain stable between runs so sessions remain valid. `OPENAI_API_KEY` is optional; without it, live AI responses are unavailable (some quiz-review paths provide a built-in fallback). Keep real secrets out of source control.

Apply the database migrations, then start Flask:

```bash
flask --app run.py db upgrade
python run.py
```

Open <http://127.0.0.1:5000/>. The configured database must be persistent: the application's fallback database is in-memory and is intended for tests, not normal local use. If you use another database, set its SQLAlchemy URL in `DATABASE_URL` and make sure its driver and service are available.

### React preview

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open <http://127.0.0.1:5173/app>. Node.js 22.12 or newer is required by the current Vite version. The preview can run without Flask, but its feature pages are not connected to backend data. The Vite development server proxies `/api` requests to Flask. Authentication and the notes contract (`GET /api/notes`, `GET /api/topics`, `POST /api/notes`, and `GET /api/notes/<id>`) are implemented; other feature pages remain placeholders. See `frontend/FRONTEND.md` for the notes API contract.

To build or locally serve the compiled preview:

```bash
npm run build
npm run preview
```

## Architecture

<!-- ```mermaid
flowchart TD
		Browser[Browser]
		FlaskUI[Flask routes and Jinja templates]
		ReactUI[React and Vite preview at /app]
		Services[Flask services]
		Models[SQLAlchemy models]
		Database[(Configured database)]
		OpenAI[OpenAI API optional]
		PDF[pypdf]

		Browser --> FlaskUI
		FlaskUI --> Services
		Services --> Models
		Models --> Database
		Services -. tutor requests .-> OpenAI
		FlaskUI -. PDF note import .-> PDF
		Browser --> ReactUI
		ReactUI -. API integration is future work .-> FlaskUI
``` -->

<!-- The Flask app is created by `app.create_app()` and launched by `run.py`. Routes handle HTTP requests and render templates or return JSON; services hold study and AI operations; SQLAlchemy models represent persisted users and study data. Flask-Migrate applies schema changes from `migrations/`.

The React app is a separate Vite frontend. `frontend/src/App.jsx` maps routes, `frontend/src/layouts/` and `frontend/src/components/` provide the shared shell, and `frontend/src/pages/` contains the current screens. `frontend/vite.config.js` reserves a development proxy for `/api`, but backend API integration and shared authentication are future work. See [frontend/README.md](frontend/README.md) and [frontend/API_REQUESTS.md](frontend/API_REQUESTS.md) for its current scope and proposed API contract. -->

## Project Layout

```text
backend/
	models/       Database models
	routes/       Flask page and JSON routes
	services/     Study, AI, document, and progress logic
	utils/        Shared validation helpers
frontend/
	src/          React app shell, pages, components, and styles
migrations/     Flask-Migrate migration scripts
templates/      Flask/Jinja HTML pages
static/         CSS and JavaScript for Flask pages
test/           pytest test suite
run.py          Flask application entry point
```

## Tests

With the Python virtual environment active, run the backend tests from the repository root:

```bash
pytest
```

## Configuration

| Variable | Purpose | Required |
| --- | --- | --- |
| `SECRET_KEY` | Signs Flask session data; configure a stable secret outside source control. | Recommended |
| `DATABASE_URL` | SQLAlchemy connection URL. Defaults to an in-memory SQLite database. | For persistent local use |
| `OPENAI_API_KEY` | Enables live OpenAI tutor responses. | No |

## Roadmap / Notes

<!-- - Connect the React preview to the Flask application and implement shared authentication.
- Replace this short list with project-specific plans, known limitations, or contribution guidance. -->
<!-- 
## Contributing

<!-- TODO: Add your preferred workflow for issues, branches, pull requests, and code style. -->

Contributions are welcome. Please open an issue to discuss larger changes before submitting a pull request. -->

<!-- ## License

<!-- TODO: Add a LICENSE file and state the project license here. -->

No license has been specified yet. -->
