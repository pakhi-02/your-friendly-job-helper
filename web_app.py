from __future__ import annotations

import os
import tempfile
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from flask import Flask, abort, render_template_string, request, send_file, url_for

from config import (
    CANDIDATE_PROFILE,
    COVER_LETTER_LENGTH,
    COVER_LETTER_TONE,
    OLLAMA_MODEL,
    OUTPUT_DIR,
)
from cover_letter import SUPPORTED_LENGTHS, SUPPORTED_TONES, normalize_length, normalize_tone
from document_loader import SUPPORTED_EXTENSIONS
from llm_client import LocalLLMClient
from main import generate_application_documents

app = Flask(__name__)
DOWNLOAD_BUNDLES: dict[str, dict[str, str]] = {}
GENERATION_HISTORY: list[dict[str, str]] = []
MAX_DOWNLOAD_BUNDLES = 50
MAX_HISTORY_ITEMS = 12

PAGE_TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Your Friendly Job Helper</title>
  <style>
    :root {
      --bg: #000000;
      --card: rgba(10, 10, 10, 0.92);
      --card-solid: #0a0a0a;
      --text: #f1f1f1;
      --muted: #9b9b9b;
      --border: rgba(255, 255, 255, 0.14);
      --primary: #4b7dff;
      --primary-dark: #3c6de8;
      --success-bg: rgba(21, 128, 61, 0.2);
      --success-text: #9ef3c0;
      --warning-bg: rgba(180, 83, 9, 0.25);
      --warning-text: #ffd9a8;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: var(--bg);
      color: var(--text);
    }
    .wrap { max-width: 1100px; margin: 28px auto; padding: 0 16px 36px; }
    .hero {
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 20px;
      box-shadow: 0 20px 40px rgba(0, 0, 0, 0.45);
      backdrop-filter: blur(6px);
      margin-bottom: 16px;
    }
    h1 { margin: 0 0 8px; font-size: 32px; line-height: 1.2; }
    .sub { margin: 0 0 12px; color: var(--muted); font-size: 16px; }
    .chips { display: flex; gap: 10px; flex-wrap: wrap; }
    .chip {
      padding: 7px 10px;
      border-radius: 999px;
      font-size: 12px;
      border: 1px solid var(--border);
      background: rgba(255, 255, 255, 0.05);
    }
    .chip.ok {
      background: var(--success-bg);
      color: var(--success-text);
      border-color: #a6f4c5;
    }
    .chip.warn {
      background: var(--warning-bg);
      color: var(--warning-text);
      border-color: #fed7aa;
    }
    .card {
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 18px;
      box-shadow: 0 16px 30px rgba(0, 0, 0, 0.4);
      backdrop-filter: blur(4px);
      margin-bottom: 16px;
    }
    .grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 14px;
    }
    .field { display: flex; flex-direction: column; gap: 6px; }
    .field.full { grid-column: 1 / -1; }
    label { font-weight: 600; font-size: 14px; }
    input[type="text"], select, textarea {
      width: 100%;
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 10px 12px;
      font-size: 14px;
      background: rgba(0, 0, 0, 0.72);
      color: var(--text);
    }
    textarea {
      min-height: 140px;
      resize: vertical;
      line-height: 1.45;
    }
    .file-box {
      border: 1px dashed rgba(255, 255, 255, 0.22);
      background: rgba(0, 0, 0, 0.65);
      border-radius: 12px;
      padding: 12px;
    }
    input[type="file"] { width: 100%; }
    .file-name {
      margin-top: 8px;
      color: var(--muted);
      font-size: 12px;
      min-height: 18px;
    }
    .actions { display: flex; gap: 10px; align-items: center; }
    button {
      border: none;
      border-radius: 10px;
      padding: 11px 16px;
      cursor: pointer;
      font-weight: 600;
      font-size: 14px;
      transition: .15s ease;
    }
    .btn-primary { background: var(--primary); color: white; }
    .btn-primary:hover { background: var(--primary-dark); }
    .btn-ghost {
      border: 1px solid var(--border);
      background: rgba(255, 255, 255, 0.03);
      color: var(--text);
      text-decoration: none;
      display: inline-block;
      padding: 10px 14px;
      border-radius: 10px;
      font-size: 13px;
      font-weight: 600;
    }
    .status-text { font-size: 13px; color: var(--muted); }
    .error {
      border: 1px solid rgba(251, 113, 133, 0.55);
      background: rgba(127, 29, 29, 0.35);
      color: #fecdd3;
      border-radius: 10px;
      padding: 10px 12px;
      font-size: 14px;
      margin-bottom: 14px;
    }
    .info {
      border: 1px solid rgba(96, 165, 250, 0.4);
      background: rgba(30, 64, 175, 0.25);
      color: #bfdbfe;
      border-radius: 10px;
      padding: 10px 12px;
      font-size: 13px;
      margin-bottom: 14px;
    }
    .metrics {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 10px;
      margin-bottom: 12px;
    }
    .metric {
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 10px;
      background: rgba(255, 255, 255, 0.02);
    }
    .metric .k { font-size: 12px; color: var(--muted); margin-bottom: 3px; }
    .metric .v { font-size: 19px; font-weight: 700; }
    .downloads { display: flex; flex-wrap: wrap; gap: 8px; margin: 10px 0; }
    .path-list { font-size: 12px; color: var(--muted); line-height: 1.5; }
    .preview-head {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 8px;
    }
    .preview-head h3 { margin: 0; font-size: 16px; }
    pre {
      margin: 0;
      background: rgba(0, 0, 0, 0.92);
      color: #ececec;
      border-radius: 12px;
      padding: 12px;
      font-size: 12px;
      line-height: 1.5;
      white-space: pre-wrap;
      max-height: 360px;
      overflow: auto;
    }
    .history-list {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 10px;
    }
    .history-item {
      border: 1px solid var(--border);
      border-radius: 12px;
      background: rgba(255, 255, 255, 0.03);
      padding: 10px;
    }
    .history-top {
      display: flex;
      justify-content: space-between;
      gap: 8px;
      margin-bottom: 6px;
      font-size: 13px;
    }
    .history-time { color: var(--muted); font-size: 11px; white-space: nowrap; }
    .history-meta { color: var(--muted); font-size: 12px; margin-bottom: 8px; }
    .history-links { display: flex; gap: 6px; flex-wrap: wrap; }
    .history-links a {
      text-decoration: none;
      color: #dbe6ff;
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 6px 8px;
      font-size: 11px;
      background: rgba(255, 255, 255, 0.03);
    }
    @media (max-width: 900px) {
      .grid, .metrics, .history-list { grid-template-columns: 1fr; }
      h1 { font-size: 26px; }
    }
  </style>
</head>
<body>
  <div class="wrap">
    <section class="hero">
      <h1>Your Friendly Job Helper</h1>
      <p class="sub">Upload resume + job description, then generate tailored notes and a custom cover letter with your local model.</p>
      <div class="chips">
        <span class="chip {{ 'ok' if llm_ok else 'warn' }}">
          LLM {{ 'Online' if llm_ok else 'Offline' }}
        </span>
        <span class="chip">Model: {{ model_name }}</span>
        <span class="chip">Formats: {{ supported_formats }}</span>
      </div>
    </section>

    <section class="card">
      {% if error %}
        <div class="error">{{ error }}</div>
      {% endif %}
      {% if info %}
        <div class="info">{{ info }}</div>
      {% endif %}

      <form id="generate-form" method="post" enctype="multipart/form-data">
        <div class="grid">
          <div class="field">
            <label for="resume_file">Resume file</label>
            <div class="file-box">
              <input id="resume_file" type="file" name="resume_file" required onchange="updateFileName('resume_file', 'resume_name')" />
              <div id="resume_name" class="file-name">No file selected</div>
            </div>
          </div>
          <div class="field">
            <label for="job_file">Job description file (optional)</label>
            <div class="file-box">
              <input id="job_file" type="file" name="job_file" onchange="updateFileName('job_file', 'job_name')" />
              <div id="job_name" class="file-name">No file selected</div>
            </div>
          </div>
          <div class="field full">
            <label for="job_description_text">Job description text</label>
            <textarea
              id="job_description_text"
              name="job_description_text"
              placeholder="Paste the full job description here. If this is filled, it will be used instead of the file."
            >{{ job_description_text }}</textarea>
          </div>
          <div class="field">
            <label for="company">Company</label>
            <input id="company" type="text" name="company" value="{{ company }}" placeholder="Acme Inc" required />
          </div>
          <div class="field">
            <label for="role">Role</label>
            <input id="role" type="text" name="role" value="{{ role }}" placeholder="Software Engineer" required />
          </div>
          <div class="field">
            <label for="candidate_name">Candidate name</label>
            <input id="candidate_name" type="text" name="candidate_name" value="{{ candidate_name }}" />
          </div>
          <div class="field">
            <label for="output_dir">Output directory</label>
            <input id="output_dir" type="text" name="output_dir" value="{{ output_dir }}" />
          </div>
          <div class="field">
            <label for="tone">Tone</label>
            <select id="tone" name="tone">
              {% for value in tones %}
                <option value="{{ value }}" {% if value == selected_tone %}selected{% endif %}>{{ value }}</option>
              {% endfor %}
            </select>
          </div>
          <div class="field">
            <label for="length">Length</label>
            <select id="length" name="length">
              {% for value in lengths %}
                <option value="{{ value }}" {% if value == selected_length %}selected{% endif %}>{{ value }}</option>
              {% endfor %}
            </select>
          </div>
        </div>

        <div class="actions" style="margin-top: 14px;">
          <button id="generate-btn" class="btn-primary" type="submit">Generate Documents</button>
          <span id="form-status" class="status-text"></span>
        </div>
      </form>
    </section>

    {% if history_entries %}
      <section class="card">
        <h2 style="margin-top: 0;">Recent Generations</h2>
        <div class="history-list">
          {% for item in history_entries %}
            <div class="history-item">
              <div class="history-top">
                <div><strong>{{ item.role }}</strong> at {{ item.company }}</div>
                <div class="history-time">{{ item.created_at }}</div>
              </div>
              <div class="history-meta">
                score {{ item.match_score }}/100 • {{ item.mode }} • {{ item.tone }}/{{ item.length }}
              </div>
              <div class="history-links">
                <a href="{{ url_for('download_file', download_id=item.download_id, file_key='notes') }}">Notes</a>
                <a href="{{ url_for('download_file', download_id=item.download_id, file_key='cover') }}">Cover</a>
                <a href="{{ url_for('download_file', download_id=item.download_id, file_key='analysis') }}">Analysis</a>
              </div>
            </div>
          {% endfor %}
        </div>
      </section>
    {% endif %}

    {% if result %}
      <section class="card">
        <h2 style="margin-top: 0;">Generation Result</h2>
        <div class="metrics">
          <div class="metric"><div class="k">Match Score</div><div class="v">{{ result.match_score }}/100</div></div>
          <div class="metric"><div class="k">Mode</div><div class="v">{{ result.generation_mode }}</div></div>
          <div class="metric"><div class="k">Tone</div><div class="v">{{ result.tone }}</div></div>
          <div class="metric"><div class="k">Length</div><div class="v">{{ result.length }}</div></div>
        </div>

        {% if download_id %}
          <div class="downloads">
            <a class="btn-ghost" href="{{ url_for('download_file', download_id=download_id, file_key='notes') }}">Download Resume Notes</a>
            <a class="btn-ghost" href="{{ url_for('download_file', download_id=download_id, file_key='cover') }}">Download Cover Letter</a>
            <a class="btn-ghost" href="{{ url_for('download_file', download_id=download_id, file_key='analysis') }}">Download Analysis JSON</a>
          </div>
        {% endif %}

        <div class="path-list">
          <div><strong>Notes:</strong> {{ result.notes_path }}</div>
          <div><strong>Cover letter:</strong> {{ result.cover_letter_path }}</div>
          <div><strong>Analysis:</strong> {{ result.analysis_path }}</div>
        </div>
      </section>

      <section class="card">
        <div class="preview-head">
          <h3>Cover Letter Preview</h3>
          <button type="button" class="btn-ghost" onclick="copyText('cover-preview')">Copy</button>
        </div>
        <pre id="cover-preview">{{ cover_letter_preview }}</pre>
      </section>

      <section class="card">
        <div class="preview-head">
          <h3>Resume Notes Preview</h3>
          <button type="button" class="btn-ghost" onclick="copyText('notes-preview')">Copy</button>
        </div>
        <pre id="notes-preview">{{ resume_notes_preview }}</pre>
      </section>
    {% endif %}
  </div>

  <script>
    function updateFileName(inputId, outputId) {
      const input = document.getElementById(inputId);
      const output = document.getElementById(outputId);
      if (!input || !output) return;
      if (input.files && input.files.length > 0) {
        output.textContent = input.files[0].name;
      } else {
        output.textContent = "No file selected";
      }
    }

    function copyText(elementId) {
      const el = document.getElementById(elementId);
      if (!el) return;
      navigator.clipboard.writeText(el.textContent || "").then(() => {
        alert("Copied to clipboard.");
      });
    }

    const form = document.getElementById("generate-form");
    const button = document.getElementById("generate-btn");
    const status = document.getElementById("form-status");
    if (form && button && status) {
      form.addEventListener("submit", function() {
        button.disabled = true;
        button.textContent = "Generating...";
        status.textContent = "This can take 10-40 seconds depending on model speed.";
      });
    }
  </script>
</body>
</html>
"""


def _is_supported_upload(filename: str) -> bool:
    """Check extension against supported document types."""
    suffix = Path(filename).suffix.lower()
    return suffix in SUPPORTED_EXTENSIONS


def _save_upload_to_temp(upload) -> str:
    """Persist uploaded file into a temporary path."""
    suffix = Path(upload.filename).suffix.lower()
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp:
        upload.save(temp.name)
        return temp.name


def _save_text_to_temp(text: str) -> str:
    """Persist plain text into a temporary .txt path."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt", mode="w", encoding="utf-8") as temp:
        temp.write(text)
        return temp.name


def _load_preview(path: str, limit_chars: int = 5000) -> str:
    """Read a generated output file preview."""
    with open(path, "r", encoding="utf-8", errors="ignore") as file:
        return file.read(limit_chars)


def _register_download_bundle(result: dict[str, str]) -> str:
    """Store generated files for secure download links."""
    download_id = uuid4().hex
    DOWNLOAD_BUNDLES[download_id] = {
        "notes": result["notes_path"],
        "cover": result["cover_letter_path"],
        "analysis": result["analysis_path"],
    }
    if len(DOWNLOAD_BUNDLES) > MAX_DOWNLOAD_BUNDLES:
        oldest_key = next(iter(DOWNLOAD_BUNDLES))
        DOWNLOAD_BUNDLES.pop(oldest_key, None)
    return download_id


def _push_history_entry(
    *,
    download_id: str,
    company: str,
    role: str,
    result: dict[str, str],
) -> None:
    """Store a compact, recent-first generation history entry."""
    entry = {
        "download_id": download_id,
        "company": company,
        "role": role,
        "match_score": result.get("match_score", "0"),
        "mode": result.get("generation_mode", "unknown"),
        "tone": result.get("tone", "formal"),
        "length": result.get("length", "medium"),
        "created_at": datetime.now().strftime("%b %d, %H:%M"),
    }
    GENERATION_HISTORY.insert(0, entry)
    del GENERATION_HISTORY[MAX_HISTORY_ITEMS:]


@app.route("/download/<download_id>/<file_key>", methods=["GET"])
def download_file(download_id: str, file_key: str):
    """Download one generated output by key."""
    bundle = DOWNLOAD_BUNDLES.get(download_id)
    if not bundle:
        abort(404)
    file_path = bundle.get(file_key)
    if not file_path or not os.path.exists(file_path):
        abort(404)
    return send_file(file_path, as_attachment=True)


@app.route("/", methods=["GET", "POST"])
def index():
    """Render form and process generation requests."""
    error = ""
    info = ""
    result = None
    download_id = ""
    cover_letter_preview = ""
    resume_notes_preview = ""

    company = request.form.get("company", "")
    role = request.form.get("role", "")
    candidate_name = request.form.get("candidate_name", CANDIDATE_PROFILE["name"])
    job_description_text = request.form.get("job_description_text", "").strip()
    selected_tone = normalize_tone(request.form.get("tone", COVER_LETTER_TONE))
    selected_length = normalize_length(request.form.get("length", COVER_LETTER_LENGTH))
    output_dir = request.form.get("output_dir", OUTPUT_DIR)

    llm_ok, llm_status = LocalLLMClient().check_health()
    if not llm_ok:
        info = (
            "Local LLM is currently offline. Generation will still work in fallback mode. "
            "Start Ollama with `ollama serve` for best quality."
        )

    if request.method == "POST":
        resume_upload = request.files.get("resume_file")
        job_upload = request.files.get("job_file")

        if not resume_upload or not resume_upload.filename:
            error = "Please upload your resume file."
        elif not _is_supported_upload(resume_upload.filename):
            supported = ", ".join(sorted(SUPPORTED_EXTENSIONS))
            error = f"Unsupported file type. Use one of: {supported}"
        elif job_upload and job_upload.filename and not _is_supported_upload(job_upload.filename):
            supported = ", ".join(sorted(SUPPORTED_EXTENSIONS))
            error = f"Unsupported job description file type. Use one of: {supported}"
        elif not job_description_text and (not job_upload or not job_upload.filename):
            error = "Provide a job description by pasting text or uploading a file."
        elif not company or not role:
            error = "Please provide both company and role."
        else:
            resume_path = ""
            job_path = ""
            try:
                resume_path = _save_upload_to_temp(resume_upload)
                if job_description_text:
                    job_path = _save_text_to_temp(job_description_text)
                else:
                    job_path = _save_upload_to_temp(job_upload)
                result = generate_application_documents(
                    resume_path=resume_path,
                    job_description_path=job_path,
                    company=company,
                    role=role,
                    output_dir=output_dir,
                    candidate_name=candidate_name,
                    tone=selected_tone,
                    length=selected_length,
                )
                download_id = _register_download_bundle(result)
                _push_history_entry(
                    download_id=download_id,
                    company=company,
                    role=role,
                    result=result,
                )
                cover_letter_preview = _load_preview(result["cover_letter_path"])
                resume_notes_preview = _load_preview(result["notes_path"])
                if result["generation_mode"] != "llm":
                    info = f"Generated in fallback mode. LLM status: {result.get('llm_status', llm_status)}"
                elif job_description_text:
                    info = "Used pasted job description text."
            except Exception as exc:
                error = f"Generation failed: {exc}"
            finally:
                for path in (resume_path, job_path):
                    if path and os.path.exists(path):
                        os.remove(path)

    return render_template_string(
        PAGE_TEMPLATE,
        error=error,
        info=info,
        result=result,
        download_id=download_id,
        cover_letter_preview=cover_letter_preview,
        resume_notes_preview=resume_notes_preview,
        company=company,
        role=role,
        candidate_name=candidate_name,
        job_description_text=job_description_text,
        tones=SUPPORTED_TONES,
        lengths=SUPPORTED_LENGTHS,
        selected_tone=selected_tone,
        selected_length=selected_length,
        output_dir=output_dir,
        url_for=url_for,
        llm_ok=llm_ok,
        model_name=OLLAMA_MODEL,
        supported_formats=", ".join(sorted(SUPPORTED_EXTENSIONS)),
        history_entries=GENERATION_HISTORY,
    )


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
