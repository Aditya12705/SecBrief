# SecBrief — all-in-one Hugging Face Space (UI + FastAPI on port 7860)

# --- Build Next.js static export ---
FROM node:20-alpine AS frontend-build
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci
COPY frontend/ ./
# Same origin: browser calls /api/* on this host
ENV NEXT_PUBLIC_API_URL=
RUN npm run build

# --- Python API + static files ---
FROM python:3.12-slim
WORKDIR /app

COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY backend/ ./backend/
COPY --from=frontend-build /app/frontend/out ./static

WORKDIR /app/backend
ENV PYTHONUNBUFFERED=1

EXPOSE 7860
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]
