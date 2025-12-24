# AI Chord Aligner

A fullstack-ready backend service that transcribes song lyrics and detects chord progressions, aligning them into a standard **lead sheet** format using AI.

## Technical Architecture

* **API:** FastAPI (Asynchronous endpoints)
* **Task Queue:** Celery + Redis (Handles high-latency AI processing)
* **Stem Separation:** Demucs (Isolates vocals for better transcription)
* **Transcription:** OpenAI Whisper (Word-level timestamps)
* **Chord Detection:** Madmom (Deep Chroma + DBN smoothing)
* **Alignment:** Custom **O(N+M)** two-pointer synchronization logic

## Prerequisites

* **Docker & Docker Compose**
* **FFmpeg** (installed automatically in the container)

## Quick Start

### 1. Clone and Setup

```bash
git clone <your-repo-url>
cd chord-aligner-ai
cp .env.example .env
```

### 2. Run with Docker

```bash
docker-compose up --build
```

### 3. Usage

* **Upload Audio:**
  `POST /upload` (mp3) → returns `task_id`
* **Check Status:**
  `GET /status/{task_id}` → returns formatted chord sheet

---

## Local Setup (No Docker)

If you prefer to run the services natively for development:

### 1. Requirements

* **FFmpeg** installed & on PATH
* **Redis** running on port `6379`
* **Python 3.10+`

### 2. Installation

```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate        # macOS/Linux
# OR
.venv\Scripts\activate           # Windows

# Install dependencies
pip install cython numpy
pip install -r requirements.txt
```

### 3. Running the App

You’ll need **two terminals**:

#### Terminal A — Celery Worker

> On Windows, `--pool=solo` is required.

```bash
celery -A workers.tasks worker --loglevel=info -P solo
```

#### Terminal B — FastAPI Server

```bash
uvicorn app.main:app --reload
```

---

## Why this Architecture?

* **Decoupled Processing**
  Whisper/Demucs are CPU-intensive. Celery prevents API timeouts & allows independent scaling.

* **Source Separation Improves Accuracy**

  * vocals → better transcription
  * instruments → better chord detection

* **Algorithmic Efficiency**
  Alignment uses a linear two-pointer search **O(N+M)** for scalability.

* **Quantized Inference**
  `compute_type="int8"` = viable performance on consumer hardware.

---

## Deployment & Resource Management

* **Memory Constraints**
  Workers typically run with `--concurrency=1` to avoid RAM thrashing on 8GB systems.

* **Model Persistence**
  Model weights should be pre-baked or stored in a persistent volume to avoid cold-starts.

* **FFmpeg Dependency**
  Installed inside Docker for consistent cross-platform behavior.
