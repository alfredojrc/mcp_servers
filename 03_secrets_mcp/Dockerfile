FROM python:3.12-slim

WORKDIR /workspace

# Install OS packages needed by backends (e.g., libkeepass might need some C libs eventually)
# RUN apt-get update && apt-get install -y --no-install-recommends ... && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod +x /workspace/entrypoint.sh

EXPOSE 5013
ENTRYPOINT ["/workspace/entrypoint.sh"] 