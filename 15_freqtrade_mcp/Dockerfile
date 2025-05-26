FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Environment variables for non-interactive setup
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on

# Install system dependencies
# - Base build tools: git, wget, build-essential
# - For TA-Lib: libta-lib0 (binary), ta-lib-dev (for compiling from source if needed)
# - For other ML libs: Check Freqtrade docs for specific C dependencies (e.g., for LightGBM, CatBoost)
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    wget \
    build-essential \
    automake \
    libtool \
    pkg-config \
    # libta-lib0 \ # No longer needed as we build from source
    # ta-lib-dev # Only if compiling TA-Lib from source and libta-lib0 is not enough
    # Add other system deps for ML libraries as needed, e.g.:
    # libgomp1 # For some ML libraries
    # cmake # For building some packages
    && rm -rf /var/lib/apt/lists/*

# (Optional but recommended) Create a non-root user for security
# RUN useradd --create-home --shell /bin/bash appuser
# USER appuser
# WORKDIR /home/appuser/app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
# It's crucial to get TA-Lib installation right.
# Option 1: If libta-lib0 is sufficient and TA-Lib pip package finds it.
# RUN pip install --no-cache-dir -r requirements.txt # No longer using this simple install


# Option 2: If TA-Lib needs to be compiled (more complex, platform-dependent)
RUN wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz && \
    tar -xzf ta-lib-0.4.0-src.tar.gz && \
    cd ta-lib/ && \
    # Download updated config.guess and config.sub and replace the old ones
    wget 'http://git.savannah.gnu.org/gitweb/?p=config.git;a=blob_plain;f=config.guess;hb=HEAD' -O 'config.guess' && \
    wget 'http://git.savannah.gnu.org/gitweb/?p=config.git;a=blob_plain;f=config.sub;hb=HEAD' -O 'config.sub' && \
    ./configure --prefix=/usr && \
    make && \
    make install && \
    ldconfig && \
    cd .. && \
    rm -rf ta-lib ta-lib-0.4.0-src.tar.gz

# Install Python TA-Lib and then other requirements
# Ensure PKG_CONFIG_PATH is set for the TA-Lib install command
RUN PKG_CONFIG_PATH=/usr/lib/pkgconfig:$PKG_CONFIG_PATH pip install --no-cache-dir TA-Lib && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Create necessary user_data directories if they don't exist from COPY
# Freqtrade will create these on first run if they are missing, but good to have placeholders
RUN mkdir -p user_data/data user_data/strategies user_data/notebooks user_data/hyperopt_results user_data/logs user_data/backtest_results
# RUN chown -R appuser:appuser user_data # If using non-root user

# Expose the port the MCP server will run on (default for FastMCP/Uvicorn is 8000)
EXPOSE 8000

# Set the entrypoint or CMD
# This will depend on how mcp_server.py is structured and run.
# Example assuming uvicorn and mcp_server:app
CMD ["uvicorn", "mcp_server:app", "--host", "0.0.0.0", "--port", "8000"] 