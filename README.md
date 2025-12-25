# AI Chord Aligner

A fullstack application that transcribes song lyrics, detects chord progressions, and aligns them into a standard **lead sheet** format using AI.

## Architecture

- **Frontend:** React (UI for uploading and viewing sheets)  
- **Backend:** FastAPI (Asynchronous REST API)  
- **Worker:** Celery + Redis (Handles background AI processing)  
- **AI Models:**
  - **Demucs:** Stems separation (isolates vocals)
  - **Whisper:** Lyrics transcription with timestamps
  - **Madmom:** Deep learning chord detection

## Prerequisites

1. **Docker & Docker Compose** (Recommended for easiest setup)  
2. **Genius API Token** (Required for lyrics fetching)  
   - Get one here: https://genius.com/api-clients

## Setup

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd chord-aligner-ai
```

### 2. Configure Environment

Create a `.env` file in the root directory:

```bash
# .env
GENIUS_API_TOKEN=your_token_here
```

---

## Option 1: Run with Docker (Recommended)

This sets up the database, backend, worker, and frontend automatically.

### Start the services

```bash
docker-compose up --build
```

### Access the App

- Frontend: http://localhost:3000  
- API Docs: http://localhost:8000/docs  

> **Note:** The `data/` folder is mounted, so processed song sheets will persist on your local machine.

---

## Option 2: Run Locally (Development)

If you need to debug specific services or don't want to use Docker, follow these steps.

### 1. External Dependencies

You must install these manually on your machine:

- **Redis:** Must be running on port `6379`  
- **FFmpeg:** Must be installed and added to your system PATH  

### 2. Backend Setup

Open a terminal for the backend:

```bash
# Create venv
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start Redis (in a separate terminal or service)
redis-server

# Start the Celery Worker
# Windows users: add --pool=solo
celery -A workers.tasks worker --loglevel=info

# Start the API Server (in a new terminal tab)
uvicorn app.main:app --reload --port 8000
```

### 3. Frontend Setup

Open a new terminal for the frontend:

```bash
cd frontend
npm install
npm start
```

The frontend will open at http://localhost:3000

It is configured to proxy API requests to http://127.0.0.1:8000 automatically.
