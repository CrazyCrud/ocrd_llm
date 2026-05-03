# @ai-generated model="Devstral-2-123B-Instruct-2512"

ARG DOCKER_BASE_IMAGE=ocrd/core:2024
FROM ${DOCKER_BASE_IMAGE}

ARG VCS_REF
ARG BUILD_DATE

LABEL \
    maintainer="https://ocr-d.de/en/contact" \
    org.opencontainers.image.title="ocrd-llm" \
    org.opencontainers.image.description="OCR-D processor: recognize text using open models via OpenAI interface" \
    org.opencontainers.image.source="https://github.com/CrazyCrud/ocrd-llm" \
    org.opencontainers.image.documentation="https://github.com/CrazyCrud/ocrd-llm" \
    org.opencontainers.image.revision=$VCS_REF \
    org.opencontainers.image.created=$BUILD_DATE \
    org.opencontainers.image.vendor="DFG-Funded Initiative for OCR-D"

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONIOENCODING=utf8
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8

# Make OCR-D resource caches predictable and writable
ENV XDG_DATA_HOME=/usr/local/share
ENV XDG_CONFIG_HOME=/usr/local/share/ocrd-resources

# Workdir for building the wheel and installing
WORKDIR /build/ocrd_llm

# Copy project into image
COPY . .

# System deps
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libgl1-mesa-glx \
        libglib2.0-0 \
        libsm6 \
        libxext6 \
        libxrender1 \
        ca-certificates \
        wget && \
    rm -rf /var/lib/apt/lists/*

# Prepackage OCR-D tool metadata
RUN ocrd ocrd-tool ocrd-tool.json dump-tools > $(dirname $(ocrd bashlib filename))/ocrd-all-tool.json && \
    ocrd ocrd-tool ocrd-tool.json dump-module-dirs > $(dirname $(ocrd bashlib filename))/ocrd-all-module-dir.json

# Install Python deps and the processor itself
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

# Clean build context
RUN rm -rf /build/ocrd_llm

# Runtime working directory and volume
WORKDIR /data
VOLUME ["/data"]

# Example:
# ocrd-llm -I OCR-D-SEG-REGION-LINES -O OCR-D-SEG-REGION-LINES-RECOGNIZED-LLM --overwrite -p '{"model_id":"qwen3.5-35b-a3b", "api_endpoint": "", "api_key": ""}'
CMD ["ocrd-llm", "--help"]
