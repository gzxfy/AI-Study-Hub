FROM python:3.14-slim

WORKDIR /app
COPY requirements.txt ./
RUN python -m pip install --no-cache-dir -r requirements.txt

COPY run.py ./
COPY backend ./backend
COPY alembic ./alembic
COPY static ./static

CMD ["sh", "-c", "python -m flask --app run.py db upgrade && exec python -m flask --app run.py run --host=0.0.0.0"]
