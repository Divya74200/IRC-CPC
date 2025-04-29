## Netcat Chat Client with Timestamped Logging

This script connects to a Netcat-based chat server and saves the chat history to a timestamped file.

### Usage

```bash
./connect.sh <server_ip> [port]
```

- `server_ip`: The IP address of the chat server (default: `127.0.0.1`)
- `port`: The port on which the server is listening (default: `12345`)

### Script

```bash
#!/usr/bin/env bash
# Usage: ./connect.sh <server_ip> [port]

HOST=${1:-127.0.0.1}
PORT=${2:-12345}

# Generate timestamped chat file name
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
CHAT_FILE="chat_history_$TIMESTAMP.txt"

echo "Connecting to $HOST:$PORT..."
echo "Saving chat to $CHAT_FILE..."

# Start a Netcat connection and log the chat
nc "$HOST" "$PORT" | tee -a "$CHAT_FILE"
```

### Output

A chat log file will be saved in the format:

```
chat_history_YYYY-MM-DD_HH-MM-SS.txt
```

Example:
```
chat_history_2025-04-29_14-35-00.txt
```
