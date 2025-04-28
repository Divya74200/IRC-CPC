#!/usr/bin/env bash
# Usage: ./connect.sh <server_ip> [port]

HOST=${1:-127.0.0.1}
PORT=${2:-12345}

echo "Connecting to $HOST:$PORT..."
nc "$HOST" "$PORT"
