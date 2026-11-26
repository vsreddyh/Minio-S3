FROM ubuntu:22.04 AS base

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y curl ca-certificates gnupg unzip \
    && rm -rf /var/lib/apt/lists/*

# Install Bun
RUN curl -fsSL https://bun.sh/install | bash

ENV PATH="/root/.bun/bin:$PATH"

WORKDIR /usr/src/app
COPY ./package*.json ./
RUN bun install

COPY . ./

# Vite inlines VITE_* variables at build time, so the API base must be supplied
# as a build argument (docker-compose passes it in).
ARG VITE_API_BASE_URL=http://localhost:8000
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
RUN bun run build

# Install a simple HTTP server
RUN bun install -g serve

EXPOSE 5173
CMD ["bunx", "serve", "dist", "-p", "5173"]