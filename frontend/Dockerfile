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
RUN bun run build

# Install a simple HTTP server
RUN bun install -g serve

EXPOSE 5173
CMD ["bunx", "serve", "dist", "-p", "5173"]