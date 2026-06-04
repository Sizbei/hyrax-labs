# ingestion-pipeline — Python multi-tool scraper
# Runs the BeautifulSoup pipeline over the bundled fixtures (no browser extras).
FROM python:3.11-slim
WORKDIR /app

COPY pyproject.toml ./
COPY src ./src
COPY fixtures ./fixtures

RUN pip install --no-cache-dir -e .

# Write the catalog to a shared volume by default (see docker-compose.yml).
CMD ["hyrax-ingest", "--fetcher", "soup", "--output", "/data/catalog.json"]
