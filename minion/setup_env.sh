#!/bin/bash
set -e

# Task 1.1 & 1.2: Environment Scripting

# Check if arguments are provided
if [ -z "$1" ]; then
  echo "Usage: $0 <repo_url> [branch]"
  exit 1
fi

REPO_URL=$1
BRANCH=${2:-main}

CONTAINER_NAME="minion-env-$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 8 | head -n 1)"

echo "==> Provisioning temporary Docker container: $CONTAINER_NAME"

# Build a generic dev container image with Goose and tools
cat << 'DOCKERFILE' > .minion.Dockerfile
FROM ubuntu:22.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y \
    curl git build-essential python3 python3-pip nodejs npm sudo \
    && rm -rf /var/lib/apt/lists/*

# Install gh cli
RUN curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg \
    && sudo chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null \
    && sudo apt update \
    && sudo apt install gh -y

# Install Goose CLI (simulated curl installer)
# For actual production, use `cargo install goose-cli` or a binary release
RUN curl -fsSL https://github.com/block/goose/releases/latest/download/goose-x86_64-unknown-linux-gnu.tar.gz | tar -xz -C /usr/local/bin || echo "Goose install simulated"

WORKDIR /workspace
DOCKERFILE

docker build -t minion-base -f .minion.Dockerfile .

echo "==> Starting container $CONTAINER_NAME"
docker run -d --name "$CONTAINER_NAME" minion-base tail -f /dev/null

echo "==> Cloning repository $REPO_URL (branch: $BRANCH)"
docker exec "$CONTAINER_NAME" bash -c "git clone --branch $BRANCH $REPO_URL repo"

echo "==> Installing dependencies"
docker exec "$CONTAINER_NAME" bash -c "
  cd repo || exit 0
  if [ -f package.json ]; then
    echo 'Found package.json, installing npm dependencies...'
    npm install
  elif [ -f requirements.txt ]; then
    echo 'Found requirements.txt, installing pip dependencies...'
    pip3 install -r requirements.txt
  else
    echo 'No known dependency file found.'
  fi
"

echo "==> Copying minion scripts into container"
docker cp minion/goose_wrapper.py "$CONTAINER_NAME":/workspace/repo/
docker cp minion/validate.py "$CONTAINER_NAME":/workspace/repo/
docker cp minion/RULES.md "$CONTAINER_NAME":/workspace/repo/
docker cp minion/hydrate_context.sh "$CONTAINER_NAME":/workspace/repo/

# Hydrate the context inside the container
docker exec "$CONTAINER_NAME" bash -c "cd /workspace/repo && chmod +x hydrate_context.sh && ./hydrate_context.sh"

echo "==> Environment ready in container $CONTAINER_NAME"
echo "$CONTAINER_NAME" > .minion_container_id
