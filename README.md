# Local LLM Resume Tailor + Cover Letter Writer

This project is now LLM-based using local inference with Ollama.

Give it:
- your resume (`.txt`, `.md`, `.pdf`, or `.docx`)
- a job description (`.txt`, `.md`, `.pdf`, or `.docx`)

It generates:
- tailored resume notes (`.md`)
- a tailored cover letter draft (`.md`)
- fit analysis output (`.json`)

## Features

- LLM-first writing flow for resume tailoring and cover letters
- Local model support through Ollama (no paid API required)
- PDF and DOCX parsing support
- Heuristic fallback if Ollama is unavailable
- Tone control for cover letters (`formal`, `concise`, `startup`)
- Length control for cover letters (`short`, `medium`, `long`)
- Local web interface for browser-based use
- Dark-themed UI with recent-generation history panel
- CLI mode and interactive mode

## Quick Start

### 1) Install dependencies

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2) Install and run Ollama

Install Ollama: [https://ollama.com/download](https://ollama.com/download)

Run Ollama server:

```bash
ollama serve
```

Pull a model (in another terminal):

```bash
ollama pull llama3.2:3b
```

### 3) Configure environment

```bash
cp .env.example .env
```

Example `.env`:

```env
CANDIDATE_NAME=Your Name
CANDIDATE_EMAIL=you@example.com
CANDIDATE_PHONE=+1-000-000-0000
CANDIDATE_LOCATION=City, Country
CANDIDATE_LINKEDIN=https://linkedin.com/in/your-profile
CANDIDATE_PORTFOLIO=https://your-portfolio.dev

OUTPUT_DIR=application_docs
TOP_KEYWORDS=20
MIN_KEYWORD_LENGTH=3
MAX_INPUT_CHARS=12000

USE_LLM=true
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:3b
LLM_TIMEOUT_SECONDS=120
LLM_TEMPERATURE=0.3
COVER_LETTER_TONE=formal
COVER_LETTER_LENGTH=medium
```

### 4) Run in CLI mode

```bash
python main.py \
  --resume-file resume.pdf \
  --job-file job_description.docx \
  --company "Acme Inc" \
  --role "Software Engineer" \
  --tone startup \
  --length short
```

### 5) Run in interactive mode

```bash
python main_simple.py
```

Tone options:
- `formal` (default)
- `concise`
- `startup`

Length options:
- `short`
- `medium` (default)
- `long`

### 6) Run web interface

```bash
python web_app.py
```

Then open [http://127.0.0.1:5000](http://127.0.0.1:5000).
After generation, use the in-page download links to save notes, cover letter, and analysis.

## Output

Files are generated under `application_docs/` (or your `OUTPUT_DIR`):
- `tailored_resume_notes_*.md`
- `cover_letter_*.md`
- `fit_analysis_*.json`

The CLI also prints:
- `Generation mode: llm` when Ollama is reachable
- `Generation mode: fallback` when it is not
- Selected cover letter tone
- Selected cover letter length


## Notes

- Quality depends on the local model you use.
- Always review and personalize generated text before applying.
- If Ollama is down, fallback mode still produces usable drafts.


#vibe coding to save time
