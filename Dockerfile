FROM python:3.11-slim

WORKDIR /app


RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*


COPY requirements.txt .
RUN pip install -U farcaster
RUN pip install nest_asyncio
RUN pip install --no-cache-dir -r requirements.txt


COPY bot.py .
COPY .env .


CMD ["python", "bot.py"]