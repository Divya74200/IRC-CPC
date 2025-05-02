import socket
import threading
server_ip='192.168.47.155'
server_port= 8000
client_socket=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
# clhiiient socket

print(f"Connecting to {server_ip}:{server_port}")
client_socket.connect(('192.168.47.155',8000))
print(f"Connected..")

def receive():
    while True:
        try:
            data=client_socket.recv(1024)
            if data:
                print(f"\n[server]:{data.decode()}")
        except:
            print(f"[!]Disconnected from the server")
            break

def send():
    while True:
        try:
            message=input("You:")
            client_socket.send(message.encode())
        except:
            break

threading.Thread(target=receive).start()
threading.Thread(target=send).start()
