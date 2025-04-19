FROM python:3.12-slim

WORKDIR /workspace

# Install OS packages if needed (e.g., for certain DB drivers)
# RUN apt-get update && apt-get install -y --no-install-recommends ... && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

# Create data directory if local backend uses it
RUN mkdir -p /data

RUN chmod +x /workspace/entrypoint.sh

EXPOSE 5012
ENTRYPOINT ["/workspace/entrypoint.sh"] 