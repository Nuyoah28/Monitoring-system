#!/bin/sh
set -eu

PROJECT_DIR="${1:-/opt/monitoring-system/backend}"
BRANCH="${2:-main}"
REPO_URL="${3:-https://github.com/Nuyoah28/Monitoring-system.git}"

if [ ! -d "$PROJECT_DIR/.git" ]; then
  echo "[deploy] 项目目录不存在，开始初始化仓库..."
  mkdir -p "$(dirname "$PROJECT_DIR")"
  git clone -b "$BRANCH" "$REPO_URL" "$PROJECT_DIR"
fi

cd "$PROJECT_DIR"

echo "[deploy] 当前目录: $PROJECT_DIR"
echo "[deploy] 更新分支: $BRANCH"
echo "[deploy] 仓库地址: $REPO_URL"

git fetch origin "$BRANCH"
git pull --ff-only origin "$BRANCH"

echo "[deploy] 使用 Jib 构建最新 Docker 镜像..."
mvn -q -DskipTests compile jib:dockerBuild

echo "[deploy] 重建后端容器..."
docker compose -f docker-compose.server.yml up -d --force-recreate backend

echo "[deploy] 部署完成"
