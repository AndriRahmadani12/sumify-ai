# Sumify AI — image untuk API dan worker.
# Basis Debian slim karena Playwright/Chromium butuh pustaka sistem yang
# tidak tersedia di image Alpine.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# ffmpeg dipakai untuk membaca berkas audio, curl untuk healthcheck.
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Unduh Chromium beserta dependensi sistemnya (dipakai untuk mencetak PDF).
RUN python -m playwright install --with-deps chromium

COPY . .

RUN mkdir -p generated_pdfs

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD curl -fsS http://localhost:8000/ || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]