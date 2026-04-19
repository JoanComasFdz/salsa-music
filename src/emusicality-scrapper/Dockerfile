FROM mcr.microsoft.com/playwright/python:v1.47.0-jammy

WORKDIR /app

# Install zip for packaging
RUN apt-get update && apt-get install -y zip && rm -rf /var/lib/apt/lists/*

# Python deps (Playwright already installed in base image)
RUN pip install --no-cache-dir playwright==1.47.0

COPY scrape.py /app/scrape.py

# Output will land here — mount this as a volume to extract the zip
VOLUME ["/out"]

ENV TARGET_URL="https://www.emusicality.co.uk/songs/babalu"
ENV PLAY_SECONDS="20"

CMD ["python", "/app/scrape.py"]
