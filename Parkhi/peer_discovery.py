import socket
import threading
from zeroconf import Zeroconf, ServiceBrowser, ServiceInfo
import uuid
import time
import json
from cryptography.fernet import Fernet

# ==== CONFIG ====
PORT = 12345
SERVICE_TYPE = "_chat._tcp.local."
UNIQUE_ID = uuid.uuid4().hex[:6]
SERVICE_NAME = f"ChatPeer-{UNIQUE_ID}.{SERVICE_TYPE}"
SHARED_KEY = b'ZpXF3voCtKInw063ekH65tcezgQIkmgRvt7jin3QDyA='  # Generate using Fernet.generate_key()    run - python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key())"
fernet = Fernet(SHARED_KEY)

# ==== GLOBALS ====
peer_sockets = {}  # key: ip:port -> socket
peer_lock = threading.Lock()
message_history = []
history_lock = threading.Lock()
MAX_HISTORY = 10
zeroconf = Zeroconf()

# ==== UTIL ====
def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    finally:
        s.close()

def serialize(obj):
    return json.dumps(obj).encode()

def deserialize(data):
    return json.loads(data.decode())

def store_message(msg):
    with history_lock:
        message_history.append(msg)
        if len(message_history) > MAX_HISTORY:
            message_history.pop(0)

def send_history(sock):
    with history_lock:
        for msg in message_history:
            try:
                sock.send(fernet.encrypt(serialize(msg)) + b'\n')
            except:
                continue

# ==== ANNOUNCE SELF ====
def announce_service():
    ip = get_ip()
    info = ServiceInfo(
        SERVICE_TYPE,
        SERVICE_NAME,
        addresses=[socket.inet_aton(ip)],
        port=PORT,
        properties={"id": UNIQUE_ID},
        server=f"chat-peer-{UNIQUE_ID}.local."
    )
    zeroconf.register_service(info)

# ==== mDNS DISCOVERY ====
class PeerListener:
    def add_service(self, zc, type, name):
        info = zc.get_service_info(type, name)
        if info:
            ip = socket.inet_ntoa(info.addresses[0])
            port = info.port
            if ip == get_ip():
                return
            peer_id = f"{ip}:{port}"
            with peer_lock:
                if peer_id in peer_sockets:
                    return
            print(f"[DISCOVERED] {peer_id}")
            connect_to_peer(ip, port)

    def remove_service(self, zc, type, name):
        print(f"[REMOVED] {name}")

def discover_peers():
    ServiceBrowser(zeroconf, SERVICE_TYPE, PeerListener())

# ==== INCOMING PEER CONNECTION ====
def listen_for_peers(port):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('', port))
    server.listen()
    print(f"[LISTENING] on port {port}")
    while True:
        try:
            conn, addr = server.accept()
            ip, port = addr
            peer_id = f"{ip}:{port}"
            with peer_lock:
                if peer_id in peer_sockets:
                    conn.close()
                    continue
                peer_sockets[peer_id] = conn
            print(f"[CONNECTED-INCOMING] {peer_id}")
            send_history(conn)
            threading.Thread(target=handle_peer, args=(conn, peer_id), daemon=True).start()
        except Exception as e:
            print(f"[LISTEN ERROR] {e}")

# ==== HANDLE PEER MESSAGES ====
def handle_peer(conn, peer_id):
    buffer = b""
    try:
        while True:
            data = conn.recv(1024)
            if not data:
                break
            buffer += data
            while b'\n' in buffer:
                line, buffer = buffer.split(b'\n', 1)
                try:
                    decrypted = fernet.decrypt(line)
                    msg = deserialize(decrypted)
                    store_message(msg)
                    if msg["id"] != UNIQUE_ID:
                        print(f"[{msg['id']}] {msg['text']}")
                        gossip_message(msg)
                except Exception as e:
                    print(f"[DECRYPT ERROR] {e}")
    except Exception as e:
        print(f"[CONN ERROR] {peer_id}: {e}")
    finally:
        print(f"[DISCONNECTED] {peer_id}")
        conn.close()
        with peer_lock:
            peer_sockets.pop(peer_id, None)

# ==== OUTGOING CONNECTION ====
def connect_to_peer(ip, port):
    peer_id = f"{ip}:{port}"
    with peer_lock:
        if peer_id in peer_sockets:
            return
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((ip, port))
        with peer_lock:
            peer_sockets[peer_id] = s
        send_history(s)
        threading.Thread(target=handle_peer, args=(s, peer_id), daemon=True).start()
        print(f"[CONNECTED-OUTGOING] {peer_id}")
    except Exception as e:
        print(f"[CONNECT ERROR] {peer_id}: {e}")

# ==== SEND MESSAGE TO ALL PEERS ====
def gossip_message(msg):
    encoded = fernet.encrypt(serialize(msg)) + b'\n'
    with peer_lock:
        for peer_id, s in list(peer_sockets.items()):
            try:
                s.send(encoded)
            except:
                print(f"[SEND FAIL] {peer_id}")
                s.close()
                peer_sockets.pop(peer_id, None)

# ==== USER CHAT MODE ====
def send_messages():
    print("[CHAT MODE] Type messages. Ctrl+C to exit.")
    try:
        while True:
            text = input()
            msg = {"id": UNIQUE_ID, "text": text, "timestamp": time.time()}
            store_message(msg)
            gossip_message(msg)
    except KeyboardInterrupt:
        print("\n[EXITING CHAT MODE]")

# ==== MAIN ====
if __name__ == "__main__":
    print(f"[BOOTING PEER] ID: {UNIQUE_ID}")
    threading.Thread(target=announce_service, daemon=True).start()
    threading.Thread(target=discover_peers, daemon=True).start()
    threading.Thread(target=listen_for_peers, args=(PORT,), daemon=True).start()

    while True:
        cmd = input("\nEnter 'chat' to start messaging: ").strip().lower()
        if cmd == 'chat':
            send_messages()
