FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt /app/requirements.txt

RUN apt-get update \
	&& apt-get install -y --no-install-recommends postgresql-client \
	&& rm -rf /var/lib/apt/lists/* \
	&& pip install --no-cache-dir -r /app/requirements.txt

# Milestone 2 runs the scrape synchronously inside the API process (moves to the
# Celery worker in M4), so the API image needs Playwright's Chromium too.
RUN playwright install --with-deps chromium

COPY backend /app/backend
COPY main.py /app/main.py
COPY alembic.ini /app/alembic.ini

COPY ./backend/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
