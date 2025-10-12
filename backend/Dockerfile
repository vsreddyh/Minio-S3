FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH=/root/.local/bin:$PATH

# System deps
RUN apt-get update && apt-get install -y \
    curl ca-certificates gnupg unzip \
    python3 python3-pip python3-venv python3-dev build-essential \
    cron \
    && rm -rf /var/lib/apt/lists/*  # [web:58][web:55]

# Install AWS CLI v2
RUN curl -sSL "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "/tmp/awscliv2.zip" \
 && unzip -q /tmp/awscliv2.zip -d /tmp \
 && /tmp/aws/install \
 && rm -rf /tmp/aws /tmp/awscliv2.zip  # configure at runtime via envs [web:35][web:34]

# Install MinIO Client (mc)
RUN curl -sSL https://dl.min.io/client/mc/release/linux-amd64/mc -o /usr/local/bin/mc \
 && chmod +x /usr/local/bin/mc  # [web:44][web:45]

WORKDIR /app1

# Python deps
COPY ./requirements.txt /app/requirements.txt
RUN pip3 install --no-cache-dir -r /app/requirements.txt  # [web:26]

# Add the alias script
COPY add_minio_s3_aliases.sh /usr/local/bin/add_minio_s3_aliases.sh
RUN chmod +x /usr/local/bin/add_minio_s3_aliases.sh  # [web:55]

# App code
COPY . /app1

# Ensure cron job script is executable
RUN chmod +x /app1/cronjob.sh

# Configure cron job to run daily at 00:00 (midnight)
# Using /etc/cron.d with explicit user field (root)
RUN echo "SHELL=/bin/bash" > /etc/cron.d/minio_sync \
 && echo "PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin" >> /etc/cron.d/minio_sync \
 && echo "0 0 * * * root /usr/local/bin/add_minio_s3_aliases.sh && /app1/cronjob.sh >> /var/log/cron.log 2>&1" >> /etc/cron.d/minio_sync \
 && chmod 0644 /etc/cron.d/minio_sync \
 && touch /var/log/cron.log

# Optional non-root
# RUN useradd -m appuser && chown -R appuser:appuser /app
# USER appuser

EXPOSE 8000

# Entrypoint: set mc aliases, then start FastAPI
ENTRYPOINT ["/bin/bash", "-lc", "/usr/sbin/cron && /usr/local/bin/add_minio_s3_aliases.sh && exec python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000"]