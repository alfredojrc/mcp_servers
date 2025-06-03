FROM python:3.10-slim

WORKDIR /workspace

# Install system dependencies for TA-Lib
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Install TA-Lib (required for technical analysis)
RUN wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz && \
    tar -xzf ta-lib-0.4.0-src.tar.gz && \
    cd ta-lib/ && \
    ./configure --prefix=/usr && \
    make && \
    make install && \
    cd .. && \
    rm -rf ta-lib ta-lib-0.4.0-src.tar.gz

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install TA-Lib Python wrapper after C library
RUN pip install --no-cache-dir TA-Lib

# Copy application files
COPY mcp_server.py .
COPY entrypoint.sh .

# Make entrypoint executable
RUN chmod +x entrypoint.sh

# Create data directories
RUN mkdir -p /workspace/data/cache /workspace/data/historical

# Expose port
EXPOSE 8017

# Set entrypoint
ENTRYPOINT ["/workspace/entrypoint.sh"]