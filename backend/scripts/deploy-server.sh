#!/bin/sh
set -eu

PROJECT_DIR="${1:-/opt/Monitoring-system}"
BRANCH="${2:-main}"
REPO_URL="${3:-https://github.com/Nuyoah28/Monitoring-system.git}"
BACKEND_DIR="$PROJECT_DIR/backend"

if [ ! -d "$PROJECT_DIR/.git" ]; then
  echo "[deploy] git repository not found under $PROJECT_DIR"
  echo "[deploy] please prepare the project on the server first"
  exit 1
fi

cd "$PROJECT_DIR"

echo "[deploy] project dir: $PROJECT_DIR"
echo "[deploy] backend dir: $BACKEND_DIR"
echo "[deploy] branch: $BRANCH"
echo "[deploy] repo: $REPO_URL"

git fetch origin "$BRANCH"
git checkout "$BRANCH"
git pull --ff-only origin "$BRANCH"

if [ ! -f "$BACKEND_DIR/pom.xml" ]; then
  echo "[deploy] backend/pom.xml not found, check SERVER_PROJECT_DIR"
  exit 1
fi

cd "$BACKEND_DIR"

if [ -x "$BACKEND_DIR/mvnw" ]; then
  MVN_CMD="./mvnw"
elif command -v mvn >/dev/null 2>&1; then
  MVN_CMD="mvn"
else
  echo "[deploy] Maven not found on server."
  echo "[deploy] Please install Maven, or add Maven Wrapper (mvnw) into backend/."
  exit 1
fi

echo "[deploy] using build command: $MVN_CMD"
echo "[deploy] building latest docker image with Jib..."
$MVN_CMD -q -DskipTests compile jib:dockerBuild

echo "[deploy] recreating backend container..."
docker compose -f docker-compose.server.yml up -d --force-recreate backend

echo "[deploy] deployment finished"
