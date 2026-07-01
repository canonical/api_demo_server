#!/usr/bin/env bash
set -euo pipefail

cleanup_docker() {
    docker compose down --volumes --remove-orphans
    docker image rm api-demo-server:integration
}

rock_path="${ROCK_PATH:-}"
if [[ -z "$rock_path" ]]; then
    set -- ./*.rock
    if [[ "$1" == "./*.rock" ]]; then
        echo "No rocks were found in $(pwd)" >&2
        exit 1
    elif [[ $# -gt 1 ]]; then
        echo "Found more than one rock $*" >&2
        exit 1
    else
        rock_path="$1"
    fi
fi
if [[ ! -f "$rock_path" ]]; then
    echo "$rock_path is not a file" >&2
    exit 1
fi

set -x
rockcraft.skopeo --insecure-policy \
    copy "oci-archive:${rock_path}" "docker-daemon:api-demo-server:integration"
trap cleanup_docker EXIT
docker compose up --detach --wait
curl --silent --fail --request POST http://localhost:8000/createtable
curl --silent --fail --request POST http://localhost:8000/addname/ --data "name=Alice"
response="$(curl --silent --fail http://localhost:8000/names)"
echo "Response: $response"
echo "$response" | grep --quiet "Alice"
