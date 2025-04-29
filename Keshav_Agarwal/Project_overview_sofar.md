Project Overview: Decentralized, Encrypted P2P Chat System
🧠 Objective

Build a fully in-house, decentralized, encrypted, terminal-based peer-to-peer (P2P) chat system, with features inspired by netcat, IRC, Matrix, and libp2p, without using any third-party cloud services or external servers.
🎯 Key Features and Functional Goals
✅ 1. Decentralized Architecture

    No centralized server.

    All peers act as both client and server (dual role).

    Peer-to-peer mesh network with optional bootstrap peer for discovery/NAT traversal.

✅ 2. Encrypted Communication

    AES-256 for encrypting messages.

    RSA or ECDH for securely exchanging AES session keys.

    Local identity via RSA keypair + UUID.

✅ 3. Persistent Local Chat Logs

    Each peer logs chat to chat_file.txt.

    Logs include: timestamp, username, uuid, message, msg_id.

    Optional encrypted log files.

✅ 4. Decentralized Chat Syncing

    When a new peer joins, it sends a SYNC_REQUEST to connected peers.

    Peers respond with a SYNC_RESPONSE containing recent messages.

    The joining peer merges the logs locally and removes duplicates using message hashes.

✅ 5. NAT Traversal (Over Internet)

    Implement UDP hole punching using a custom lightweight bootstrap peer.

    Bootstrap peer is not a relay or central node — just helps coordinate initial connections.

✅ 6. Peer Discovery

    Via LAN broadcast, static list, or custom DHT (Distributed Hash Table).

    DHT enables discovery without central control.

✅ 7. Terminal-Based CLI Interface

    All chat operations happen via terminal (e.g., python main.py).

    Future: extend to GUI or web using same backend modules.

🛠 Project Phases (Ordered for Practical Development)
📦 Phase 1: LAN Communication, No Encryption

    Create TCP server on one peer (listen mode)

    Create TCP client on another peer (connect mode)

    Enable bi-directional message flow using threads or asyncio

    Implement local chat logging (append-only file)

    Optional: support multiple clients on the server

🔐 Phase 2: Add Identity and Encryption

    Generate and save local RSA keypair + UUID

    Use RSA to exchange AES session key

    Encrypt/decrypt messages using AES

    Optionally encrypt chat_file.txt

🌐 Phase 3: Make It Decentralized

    Introduce SYNC_REQUEST/SYNC_RESPONSE protocol:

        New peer asks for messages newer than a given timestamp

        Peers respond with a filtered message list

        Peer merges messages based on msg_id hash

    Add peer-to-peer discovery:

        Use LAN discovery, static list, or your own DHT

    Use NAT traversal techniques:

        UDP hole punching

        Optional bootstrap peer to exchange IP:port info

🔁 Phase 4: Reliability & Extensibility

    Implement backup and restore of chat logs

    Add HMAC and replay protection

    Add optional features:

        File transfer

        CLI UX improvements (rich display)

        Join links like:

        p2pchat://192.168.1.50:5050?auth=secret

🔁 SYNC ARCHITECTURE EXPLAINED

When a peer joins:
Step	Action
1	Peer connects to others using IP/DHT
2	Sends SYNC_REQUEST with last known timestamp
3	Each peer returns SYNC_RESPONSE with new messages
4	New peer merges them into its log
5	Sync is complete — no need for server push

This puts sync responsibility on the joining peer, which reduces load and supports decentralization.
📂 Message Structure Example

{
  "type": "CHAT",
  "uuid": "peer-uuid-1",
  "username": "alice",
  "timestamp": "2025-04-29T14:20:00Z",
  "message": "Hello!",
  "msg_id": "SHA256(uuid + timestamp + message)"
}

💡 Why It’s Decentralized (Even with a Server)

    Any peer can act as a temporary bootstrap node

    There is no permanent server

    No peer is required to be “always on”

    Messages are always exchanged peer-to-peer, not relayed

🔒 Security Highlights

    E2E encryption (AES over RSA)

    Per-message HMAC and signature validation

    Optional encrypted local storage

    Replay protection via timestamp/nonce

📊 Difficulty & Learning Scope
🔥 Difficulty: 8.5/10

You will work with:

    Networking (TCP/UDP)

    Cryptography (RSA, AES, hashing)

    File I/O and logging

    Concurrency (threads/async)

    NAT traversal techniques

    Decentralized architecture

But you’ll also build:

    A real-world, privacy-respecting alternative to chat apps

    A great portfolio piece in cybersecurity, backend, or systems engineering

🧱 Building Blocks Used
Tech Area	Details
Language	Python 3.x
Networking	TCP/UDP sockets
Crypto	cryptography or pure Python
Storage	JSON or plaintext logs
CLI Interface	rich, curses, or plain CLI
Sync Logic	Timestamp + message hash
