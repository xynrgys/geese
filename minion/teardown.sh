#!/bin/bash
set -e

# Task 1.3: Implement an automated "Post-Run" cleanup to snapshot the diff and teardown the environment.

if [ ! -f .minion_container_id ]; then
    echo "No .minion_container_id found. Cannot teardown."
    exit 0
fi

CONTAINER_NAME=$(cat .minion_container_id)

echo "==> Snapshotting diff from container $CONTAINER_NAME"
docker exec "$CONTAINER_NAME" bash -c "cd repo && git diff" > minion_snapshot.diff || true

echo "==> Tearing down environment: $CONTAINER_NAME"
docker stop "$CONTAINER_NAME" || true
docker rm "$CONTAINER_NAME" || true

rm .minion_container_id
echo "==> Teardown complete. Diff saved to minion_snapshot.diff"