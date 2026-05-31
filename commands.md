# Commands Reference

Every command for this project, grouped by task. Replace example paths/URLs with your own.

---

## 1. Local setup

```bash
# Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt

# Install the browser used for auto-apply (one time)
python -m playwright install chromium

# Create your config from the template, then edit it
cp .env.example .env
```

---

## 2. Ollama (local model server)

```bash
# Start the Ollama server (leave running in its own terminal)
ollama serve

# Pull a model (one time)
ollama pull llama3.2:3b

# List installed models
ollama list
```

---

## 3. Generate documents (CLI)

```bash
# Basic generation
python main.py \
  --resume-file resume.pdf \
  --job-file job_description.docx \
  --company "Acme Inc" \
  --role "Software Engineer"

# With tone and length options
python main.py \
  --resume-file resume.pdf \
  --job-file job_description.docx \
  --company "Acme Inc" \
  --role "Software Engineer" \
  --tone startup \
  --length short
```

Tone: `formal` | `concise` | `startup`  •  Length: `short` | `medium` | `long`

---

## 4. Interactive mode

```bash
python main_simple.py
```

---

## 5. Web app (local)

```bash
python web_app.py
# then open http://127.0.0.1:5000
```

---

## 6. Auto-apply (browser automation)

```bash
# Fill the form + screenshot, then STOP for review (safe default)
python auto_apply.py \
  --url "https://boards.greenhouse.io/acme/jobs/123456" \
  --resume-file resume.pdf \
  --cover-letter-file application_docs/cover_letter_acme_software_engineer_*.md \
  --company "Acme Inc" \
  --role "Software Engineer"

# Same, but actually submit
python auto_apply.py \
  --url "https://boards.greenhouse.io/acme/jobs/123456" \
  --resume-file resume.pdf \
  --cover-letter-file application_docs/cover_letter_*.md \
  --company "Acme Inc" --role "Software Engineer" \
  --submit

# Generate AND apply in one command
python main.py \
  --resume-file resume.pdf --job-file job_description.docx \
  --company "Acme Inc" --role "Software Engineer" \
  --apply-url "https://boards.greenhouse.io/acme/jobs/123456"
  # add --submit to send automatically
```

> Keep `AUTO_SUBMIT=false` until you trust the output. `--submit` overrides it for one run.

---

## 7. Docker (local or hosted)

```bash
# Configure first
cp .env.example .env            # edit profile + set APP_PASSWORD to enable login

# Build and start (web app + Ollama)
docker compose up --build -d

# Pull a model into the Ollama container (one time)
docker compose exec ollama ollama pull llama3.2:3b

# Open the app
open http://localhost:5000      # macOS (Linux: xdg-open)

# View logs
docker compose logs -f web
docker compose logs -f ollama

# Restart just the web app after a code change
docker compose up --build -d web

# Stop everything
docker compose down             # add -v to also delete the model volume
```

### With HTTPS (Caddy reverse proxy)

The `caddy` service in compose terminates HTTPS and proxies to the web app.

```bash
# Local testing (locally-trusted self-signed cert)
# set DOMAIN=localhost in .env, then:
docker compose up --build -d
open https://localhost          # accept the local cert warning once

# Hosted with a real domain (DNS A record pointed at the server)
# set DOMAIN=jobs.example.com and ACME_EMAIL=you@example.com in .env, then:
docker compose up --build -d    # Caddy fetches a free Let's Encrypt cert automatically
```

Ports 80/443 must be reachable for the public cert to be issued. The web app is
only exposed on `127.0.0.1:5000` (direct, for debugging); Caddy is the front door.

---

## 8. Build / run the image manually (without compose)

```bash
# Build
docker build -t job-helper .

# Run (point at an Ollama reachable from the container)
docker run --rm -p 5000:5000 --env-file .env \
  -e OLLAMA_BASE_URL=http://host.docker.internal:11434 \
  -v "$(pwd)/application_docs:/app/application_docs" \
  job-helper
```

---

## 9. Publishing the image (GHCR)

The GitHub Actions workflow (`.github/workflows/docker-publish.yml`) builds and
pushes automatically on every push to `main` and on version tags. To cut a
release image manually:

```bash
git tag v1.0.0
git push origin v1.0.0          # triggers the workflow -> ghcr.io/<owner>/<repo>:1.0.0
```

Pull a published image:

```bash
docker pull ghcr.io/<owner>/<repo>:latest
```

---

## 10. Authentication

Set these in `.env` (or the host's environment) before exposing the web app:

```bash
APP_USERNAME=admin
APP_PASSWORD=choose-a-strong-password   # empty = auth disabled (local only)
```

The app then prompts for username/password (HTTP Basic Auth) on every request.
