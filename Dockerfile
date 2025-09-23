FROM python:3.10-slim

LABEL MAINTAINER="Igor Muravsky <muravsky@gmail.com>"
LABEL NAME=vmware_exporter
LABEL VERSION="1.0"

# Install required packages first
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        ca-certificates \
        wget \
        gcc \
        python3-dev \
        libffi-dev \
        libssl-dev && \
    rm -rf /var/lib/apt/lists/*

# Create non-root user for security with simpler command
RUN groupadd -r vmware && \
    useradd -r -g vmware -d /opt/vmware_exporter -s /sbin/nologin vmware

WORKDIR /opt/vmware_exporter/

# Copy requirements first for better layer caching
COPY requirements.txt /opt/vmware_exporter/

# Install Python packages
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . /opt/vmware_exporter/

# Install the application
RUN pip install --no-cache-dir .

# Change ownership to non-root user
RUN chown -R vmware:vmware /opt/vmware_exporter

USER vmware

EXPOSE 9272

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:9272/healthz || exit 1

ENTRYPOINT ["/usr/local/bin/vmware_exporter"]