#!/bin/sh
set -eu

PROJECT_DIR="${1:-/opt/Monitoring-system}"
BRANCH="${2:-main}"
REPO_URL="${3:-https://github.com/Nuyoah28/Monitoring-system.git}"
BACKEND_DIR="$PROJECT_DIR/backend"
DEPLOY_MODE="${4:-docker}"
LOG_DIR="$BACKEND_DIR/logs"
RUN_DIR="$BACKEND_DIR/run"
PID_FILE="$RUN_DIR/backend.pid"

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
echo "[deploy] mode: $DEPLOY_MODE"

git fetch origin "$BRANCH"
git checkout "$BRANCH"
git pull --ff-only origin "$BRANCH"

if [ ! -f "$BACKEND_DIR/pom.xml" ]; then
  echo "[deploy] backend/pom.xml not found, check SERVER_PROJECT_DIR"
  exit 1
fi

cd "$BACKEND_DIR"
mkdir -p "$LOG_DIR" "$RUN_DIR"

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

if [ "$DEPLOY_MODE" = "docker" ]; then
  echo "[deploy] building latest docker image with Jib..."
  $MVN_CMD -q -DskipTests compile jib:dockerBuild

  echo "[deploy] recreating backend container..."
  docker compose -f docker-compose.server.yml up -d --force-recreate backend
elif [ "$DEPLOY_MODE" = "process" ]; then
  LOG_FILE="$LOG_DIR/backend-$(date +%Y%m%d-%H%M%S).log"
  echo "[deploy] packaging Spring Boot jar..."
  $MVN_CMD -q -DskipTests clean package

  APP_JAR="$(find "$BACKEND_DIR/target" -maxdepth 1 -type f -name "*.jar" ! -name "*original*.jar" | head -n 1)"
  if [ -z "$APP_JAR" ]; then
    echo "[deploy] packaged jar not found under $BACKEND_DIR/target"
    exit 1
  fi

  if [ -f "$PID_FILE" ]; then
    OLD_PID="$(cat "$PID_FILE" 2>/dev/null || true)"
    if [ -n "$OLD_PID" ] && kill -0 "$OLD_PID" 2>/dev/null; then
      echo "[deploy] stopping old backend process: $OLD_PID"
      kill "$OLD_PID"
      sleep 5
      if kill -0 "$OLD_PID" 2>/dev/null; then
        echo "[deploy] old process still alive, forcing stop"
        kill -9 "$OLD_PID"
      fi
    fi
    rm -f "$PID_FILE"
  fi

  echo "[deploy] starting backend process..."
  nohup java -jar "$APP_JAR" --spring.profiles.active=prod >> "$LOG_FILE" 2>&1 &
  NEW_PID=$!
  echo "$NEW_PID" > "$PID_FILE"
  ln -sfn "$(basename "$LOG_FILE")" "$LOG_DIR/current.log"
  echo "[deploy] backend pid: $NEW_PID"
  echo "[deploy] backend log: $LOG_FILE"
else
  echo "[deploy] unsupported DEPLOY_MODE: $DEPLOY_MODE"
  echo "[deploy] supported modes: docker, process"
  exit 1
fi

echo "[deploy] deployment finished"
