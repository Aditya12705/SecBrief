# SecBrief — all-in-one Hugging Face Space (UI + FastAPI on port 7860)

# --- Build Next.js static export ---
FROM node:20-alpine AS frontend-build
WORKDIR /app/frontend

# Cache-bust when frontend source changes (set by HF build or default)
ARG CACHEBUST=1

COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci

COPY frontend/ ./
# Never ship stale export from git; always rebuild from source
RUN rm -rf .next out
ENV NEXT_PUBLIC_API_URL=
RUN npm run build

# --- Python API + static files ---
FROM python:3.12-slim
WORKDIR /app

COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY backend/ ./backend/
COPY --from=frontend-build /app/frontend/out ./static

# Build marker — check /health → frontend_build_sha after deploy
RUN date -u +"%Y-%m-%dT%H:%MZ" > /app/static/.build-sha

WORKDIR /app/backend
ENV PYTHONUNBUFFERED=1

EXPOSE 7860
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]
