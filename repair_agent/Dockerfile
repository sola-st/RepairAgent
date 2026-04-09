# RepairAgent Docker image
# Includes Java 11, Perl, Defects4J, and all Python dependencies.
#
# Build:  docker build -t repairagent .
# Run:    docker run --rm -e OPENAI_API_KEY=... repairagent run --bugs "Chart 1" --model gpt-4o-mini

FROM python:3.10-slim

# Install system dependencies:
#   - Java 11 (required for Defects4J)
#   - Perl + modules (required for Defects4J)
#   - Build tools and utilities
#   - Browsers (for web commands, if needed)
RUN apt-get update && apt-get install -y \
    openjdk-11-jdk \
    perl cpanminus libdbi-perl \
    subversion dos2unix git curl jq wget \
    chromium-driver firefox-esr ca-certificates \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV PIP_NO_CACHE_DIR=yes \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64

ENV PATH="$PATH:/root/.local/bin"

WORKDIR /app

# Install Python requirements first (layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Clone and initialize Defects4J if not already present in build context
RUN if [ ! -d "defects4j/framework" ]; then \
        rm -rf defects4j && \
        git clone https://github.com/rjust/defects4j.git && \
        cd defects4j && cpanm --installdeps . && cpanm String::Interpolate && ./init.sh ; \
    fi

# Add Defects4J to PATH
ENV PATH="$PATH:/app/defects4j/framework/bin"

ENTRYPOINT ["python3", "repairagent.py"]
CMD ["run"]
