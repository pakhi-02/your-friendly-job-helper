# Playwright's official image ships Chromium + all OS libraries the browser needs,
# so auto-apply works in the container without extra apt installs.
FROM mcr.microsoft.com/playwright/python:v1.49.0-jammy

WORKDIR /app

# Install Python deps first so this layer is cached across code changes.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && python -m playwright install chromium

COPY . .

# In a container there is no display, so the browser must run headless.
ENV APPLY_HEADLESS=true \
    FLASK_HOST=0.0.0.0 \
    FLASK_PORT=5000 \
    PYTHONUNBUFFERED=1

EXPOSE 5000

# Single worker + threads: the app keeps download/history state in memory, so it
# must not be split across processes. Long timeout because auto-apply drives a
# real browser session.
CMD ["gunicorn", "--workers", "1", "--threads", "4", "--timeout", "300", \
     "--bind", "0.0.0.0:5000", "web_app:app"]
