#!/usr/bin/env bash
set -xeuo pipefail

cleanup_docker() {
    docker compose down --volumes --remove-orphans
}

trap cleanup_docker EXIT
docker compose up --detach --wait
curl --silent --fail --request POST http://localhost:8000/createtable
curl --silent --fail --request POST http://localhost:8000/addname/ --data "name=Alice"
response="$(curl --silent --fail http://localhost:8000/names)"
echo "Response: $response"
echo "$response" | grep --quiet "Alice"
