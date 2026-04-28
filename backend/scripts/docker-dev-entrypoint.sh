#!/bin/sh
set -eu

cd /workspace

snapshot() {
  find pom.xml src/main/java src/main/resources -type f -printf '%p %T@\n' 2>/dev/null | sort
}

echo "[docker-dev] preparing initial compilation..."
mkdir -p src/main/resources
touch src/main/resources/.reloadtrigger
mvn -q -DskipTests compile resources:resources

echo "[docker-dev] starting Spring Boot with profile docker-dev..."
mvn -q -DskipTests spring-boot:run -Dspring-boot.run.fork=true -Dspring-boot.run.profiles=docker-dev &
APP_PID=$!

LAST_STATE="$(snapshot)"

while kill -0 "$APP_PID" 2>/dev/null; do
  sleep 2
  NEW_STATE="$(snapshot)"
  if [ "$NEW_STATE" != "$LAST_STATE" ]; then
    LAST_STATE="$NEW_STATE"
    echo "[docker-dev] source changed, recompiling..."
    mvn -q -DskipTests compile resources:resources
    touch src/main/resources/.reloadtrigger
  fi
done

wait "$APP_PID"

