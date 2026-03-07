#!/bin/bash
set -e

# Task 1.1 & 1.2: Environment Scripting
# "Write a bash script that provisions a temporary Docker container, clones my current repo, and installs all devDependencies."

# Check if arguments are provided
if [ -z "$1" ]; then
  echo "Usage: $0 <repo_url> [branch]"
  exit 1
fi

REPO_URL=$1
BRANCH=${2:-main}

CONTAINER_NAME="minion-env-$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 8 | head -n 1)"

echo "==> Provisioning temporary Docker container: $CONTAINER_NAME"

# Build a generic dev container image
cat << 'DOCKERFILE' > .minion.Dockerfile
FROM ubuntu:22.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y \
    curl git build-essential python3 python3-pip nodejs npm sudo \
    && rm -rf /var/lib/apt/lists/*

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

echo "==> Environment ready in container $CONTAINER_NAME"
echo "$CONTAINER_NAME" > .minion_container_id
