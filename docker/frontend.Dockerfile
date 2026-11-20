FROM node:24-slim

WORKDIR /app
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend/index.html frontend/vite.config.js ./
COPY frontend/src ./src

CMD ["./node_modules/.bin/vite", "--host", "0.0.0.0"]
