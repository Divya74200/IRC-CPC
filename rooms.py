# IRC-style enhanced version of your LAN chat with multi-room support and LAN IP binding
import socket
import threading
import uuid
import json
import os
import time
from datetime import datetime
from cryptography.fernet import Fernet
from zeroconf import Zeroconf, ServiceInfo, ServiceBrowser

room_password = input("Enter room password: ").strip()
current_room = input("Enter room name (default=#general): ") or "#general"
peer_name = input("Enter your name: ").strip() or uuid.uuid4().hex[:4]
print(f"[INFO] You are '{peer_name}' in room '{current_room}'")

peer_id = peer_name
key = Fernet.generate_key()
fernet = Fernet(key)

# === Get LAN IP ===
def get_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

local_ip = get_ip()
peer_sockets = {}
peer_sockets_lock = threading.Lock()
rooms = {current_room: set()}  # room_name -> peer_ids
chat_logs = {}  # room_name -> filename
chat_log_lock = threading.Lock()
zeroconf = Zeroconf()

# === Chat Logging ===
def get_log_file(room):
    fname = f"chat_{room}.log"
    if room not in chat_logs:
        chat_logs[room] = fname
    return fname

def print_history(room):
    fname = get_log_file(room)
    if os.path.exists(fname):
        print(f"[HISTORY] Messages from {fname}:")
        with open(fname, "r") as f:
            for line in f:
                print(line.strip())
        print("=" * 50)

print_history(current_room)

# === Server ===
def start_tcp_server():
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.bind((local_ip, 0))
    server_sock.listen(5)
    port = server_sock.getsockname()[1]
    print(f"[SERVER] Listening on {local_ip}:{port}")

    desc = {"peer_name": peer_name, "room": current_room}
    info = ServiceInfo(
        "_chat._tcp.local.",
        f"{peer_name}._chat._tcp.local.",
        addresses=[socket.inet_aton(local_ip)],
        port=port,
        properties=desc,
    )
    zeroconf.register_service(info)

    try:
        while True:
            conn, addr = server_sock.accept()
            threading.Thread(target=handle_peer_conn, args=(conn, addr), daemon=True).start()
    finally:
        zeroconf.unregister_service(info)
        zeroconf.close()
        server_sock.close()

# === Handle Connection ===
def handle_peer_conn(conn, addr):
    try:
        data = conn.recv(4096).decode()
        join_req = json.loads(data)

        room = join_req.get("room")
        if join_req.get("password") != room_password:
            conn.sendall(json.dumps({"status": "reject"}).encode())
            conn.close()
            return

        remote_id = join_req.get("id")
        if remote_id == peer_name:
            conn.sendall(json.dumps({"status": "reject_duplicate"}).encode())
            conn.close()
            return

        conn.sendall(json.dumps({"status": "accepted", "id": peer_name}).encode())

        with peer_sockets_lock:
            peer_sockets[remote_id] = conn
        rooms.setdefault(room, set()).add(remote_id)

        threading.Thread(target=handle_peer, args=(remote_id, conn, room), daemon=True).start()

    except Exception as e:
        print(f"[ERROR] handle_peer_conn: {e}")
        conn.close()

# === Handle Messages ===
def handle_peer(remote_id, conn, room):
    try:
        while True:
            data = conn.recv(1024)
            if not data:
                break
            msg = data.decode().strip()
            ts = datetime.now().strftime("%H:%M")
            formatted = f"[{ts}] {remote_id}: {msg}"
            print(formatted)
            with chat_log_lock:
                with open(get_log_file(room), "a") as f:
                    f.write(formatted + "\n")
            broadcast(formatted, room, exclude=remote_id)
    except:
        pass
    finally:
        print(f"[DISCONNECTED] {remote_id}")
        with peer_sockets_lock:
            peer_sockets.pop(remote_id, None)
        rooms[room].discard(remote_id)
        conn.close()

# === Broadcast ===
def broadcast(msg, room, exclude=None):
    with peer_sockets_lock:
        for pid, sock in peer_sockets.items():
            if pid == exclude or pid not in rooms.get(room, set()):
                continue
            try:
                sock.sendall(msg.encode() + b"\n")
            except:
                continue
    with chat_log_lock:
        with open(get_log_file(room), "a") as f:
            f.write(msg + "\n")

# === Zeroconf Discovery ===
class RoomListener:
    def add_service(self, zeroconf, type, name):
        info = zeroconf.get_service_info(type, name)
        if not info:
            return
        ip = socket.inet_ntoa(info.addresses[0])
        port = info.port
        props = info.properties
        room = props.get(b"room", b"").decode()
        rid = props.get(b"peer_name", b"").decode()

        if room == current_room and rid != peer_name:
            time.sleep(0.5)  # Ensure peer's server is ready
            threading.Thread(target=connect_to_peer, args=(ip, port, room, rid), daemon=True).start()

    def remove_service(self, zeroconf, type, name):
        pass

    def update_service(self, zeroconf, type, name):
        pass

def connect_to_peer(ip, port, room, rid):
    try:
        with peer_sockets_lock:
            if rid in peer_sockets:
                return
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((ip, port))
        join = {"room": room, "password": room_password, "id": peer_name}
        sock.sendall(json.dumps(join).encode())
        raw = sock.recv(4096)
        res = json.loads(raw.decode())
        if res.get("status") == "accepted":
            with peer_sockets_lock:
                peer_sockets[rid] = sock
            rooms.setdefault(room, set()).add(rid)
            threading.Thread(target=handle_peer, args=(rid, sock, room), daemon=True).start()
    except Exception as e:
        print(f"[ERROR] connect_to_peer: {e}")

# === Input Handler ===
def input_loop():
    global current_room
    print("[CHAT] Enter messages or IRC-style commands like /join #room, /who, /msg text")
    while True:
        try:
            line = input()
            if not line.strip():
                continue
            if line.startswith("/join"):
                _, room = line.strip().split(maxsplit=1)
                current_room = room.strip()
                rooms.setdefault(current_room, set())
                print_history(current_room)
                print(f"[INFO] Switched to {current_room}")
            elif line.startswith("/who"):
                peers = rooms.get(current_room, set())
                print(f"[PEERS in {current_room}]: {', '.join(peers) if peers else 'No one'}")
            else:
                ts = datetime.now().strftime("%H:%M")
                msg = f"[{ts}] {peer_name}: {line}"
                print(f"[YOU] {msg}")
                broadcast(msg, current_room)
        except KeyboardInterrupt:
            print("\n[EXIT] Bye!")
            os._exit(0)

if __name__ == "__main__":
    listener = RoomListener()
    ServiceBrowser(zeroconf, "_chat._tcp.local.", listener)
    threading.Thread(target=start_tcp_server, daemon=True).start()
    input_loop()
