# ─── Base Image ───────────────────────────────────────────────────────────────
FROM python:3.11-slim

# ─── Metadata ─────────────────────────────────────────────────────────────────
LABEL maintainer="someattachment"
LABEL description="Telegram Clone Bot System"

# ─── Environment Variables ────────────────────────────────────────────────────
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    TZ=Asia/Kolkata

# ─── System Dependencies ──────────────────────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    tzdata \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime \
    && echo $TZ > /etc/timezone

# ─── Working Directory ────────────────────────────────────────────────────────
WORKDIR /app

# ─── Python Dependencies (cache layer optimize) ───────────────────────────────
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ─── Application Code ─────────────────────────────────────────────────────────
COPY bot.py .

# ─── Persistent Data Volume ───────────────────────────────────────────────────
# cloned_bots.json yahan persist hoga
VOLUME ["/app/data"]

# JSON file ko data folder mein link kar do taaki container restart pe data bach jaaye
ENV DATA_FILE=/app/data/cloned_bots.json

# ─── Non-root User (security) ─────────────────────────────────────────────────
RUN useradd -m -u 1000 botuser && \
    mkdir -p /app/data && \
    chown -R botuser:botuser /app
USER botuser

# ─── Healthcheck ──────────────────────────────────────────────────────────────
HEALTHCHECK --interval=60s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import os; exit(0 if os.path.exists('/app/bot.py') else 1)"

# ─── Run ──────────────────────────────────────────────────────────────────────
CMD ["python", "-u", "bot.py"]
