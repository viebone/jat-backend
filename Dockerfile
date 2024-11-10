FROM python:3.12.4 AS builder

# Install dependencies in a virtual environment
WORKDIR /app
RUN python -m venv /opt/venv
COPY requirements.txt ./
RUN /opt/venv/bin/pip install -r requirements.txt

# Copy application files
COPY . .

# Use the virtual environment path and simplify the startup command
FROM python:3.12.4-slim
WORKDIR /app
COPY --from=builder /app /app
COPY --from=builder /opt/venv /opt/venv

# Activate the virtual environment
ENV PATH="/opt/venv/bin:$PATH"

# Start with gunicorn in the main path
CMD ["gunicorn", "-w", "1", "-k", "gevent", "-b", "0.0.0.0:8080", "wsgi:app"]
