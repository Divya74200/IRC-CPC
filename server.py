#!/usr/bin/env python3
import socket
import select

HOST = '0.0.0.0'
PORT = 12345

# Broadcast a message to all clients (optionally excluding one)
def broadcast(message, exclude_sock=None):
    for client_sock, _ in clients:
        if client_sock != exclude_sock:
            try:
                client_sock.sendall(message.encode() if isinstance(message, str) else message)
            except Exception:
                pass

# Set up the listening socket
server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_sock.bind((HOST, PORT))
server_sock.listen()
print(f"Server listening on {HOST}:{PORT}")

clients = []  # List of (socket, username)

try:
    while True:
        # Wait for activity on server or client sockets
        ready_to_read, _, _ = select.select([server_sock] + [sock for sock, _ in clients], [], [])
        for sock in ready_to_read:
            if sock is server_sock:
                # New connection
                conn, addr = server_sock.accept()
                conn.sendall(b"Enter your username: ")
                name = conn.recv(1024).decode().strip()
                welcome = f"*** {name} has joined the chat ***\n"
                broadcast(welcome)
                clients.append((conn, name))
                print(welcome.strip())
            else:
                # Incoming message or disconnect
                data = sock.recv(4096)
                if not data:
                    # Client disconnected
                    for i, (c, uname) in enumerate(clients):
                        if c is sock:
                            farewell = f"*** {uname} has left the chat ***\n"
                            broadcast(farewell, exclude_sock=sock)
                            print(farewell.strip())
                            clients.pop(i)
                            break
                    sock.close()
                else:
                    # Broadcast message
                    sender = next(uname for c, uname in clients if c is sock)
                    message = f"{sender}: {data.decode()}"
                    broadcast(message)
                    print(message.strip())
except KeyboardInterrupt:
    print("\nServer shutting down.")
    for sock, _ in clients:
        sock.close()
    server_sock.close()
