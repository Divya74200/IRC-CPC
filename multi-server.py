import socket
import threading

HOST = '0.0.0.0'
PORT = 8000

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen(5)
print("Server listening on port", PORT)

clients = []

def broadcast(message, sender_conn=None):
    for conn, _ in clients:
        try:
            conn.sendall(message)
        except:
            conn.close()
            clients.remove((conn, _))

def handle_client(conn, addr):
    print(f"[+] New connection from {addr}")
    while True:
        try:
            data = conn.recv(1024)
            if not data:
                break
            print(f"[{addr}]: {data.decode()}")
            broadcast(data, conn)
        except:
            break
    print(f"[-] Connection from {addr} closed")
    conn.close()
    clients.remove((conn, addr))

def accept_connections():
    while True:
        conn, addr = server.accept()
        clients.append((conn, addr))
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()

def send_from_server():
    while True:
        try:
            msg = input()
            if msg:
                full_msg = f"[Server]: {msg}".encode()
                broadcast(full_msg)
        except:
            break

# Start thread to accept incoming clients
threading.Thread(target=accept_connections, daemon=True).start()

# Main thread handles server's input
send_from_server()
