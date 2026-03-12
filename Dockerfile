FROM --platform=linux/amd64 python:3.12-slim-bookworm

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    unzip \
    graphviz \
    graphviz-dev \
    gcc \
    g++ \
    pkg-config \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Echidna
RUN wget -qO /tmp/echidna.zip \
    https://github.com/crytic/echidna/releases/download/v2.2.1/echidna-2.2.1-Linux.zip \
    && unzip /tmp/echidna.zip -d /tmp/echidna \
    && tar -xzf /tmp/echidna/echidna.tar.gz -C /usr/local/bin \
    && chmod +x /usr/local/bin/echidna \
    && rm -rf /tmp/echidna /tmp/echidna.zip

# Install solc
RUN pip install --no-cache-dir solc-select \
    && solc-select install 0.8.20 \
    && solc-select use 0.8.20

    
COPY . .
    
RUN pip install --no-cache-dir -r requirements.txt

WORKDIR /app

ENTRYPOINT ["python", "fuzz4pa.py"]