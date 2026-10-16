FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev curl \
    libcairo2 libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf-2.0-0 \
    libffi-dev shared-mime-info \
    libreoffice-core libreoffice-writer \
    fonts-liberation fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

# LaTeX rendering is stubbed by default. To enable, uncomment and rebuild
# (~700MB extra): install texlive-latex-recommended texlive-fonts-recommended
# and set APP_PDF_LATEX_ENABLED=true.

WORKDIR /app

COPY . .
RUN pip install --upgrade pip && pip install -e ".[dev]"

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
