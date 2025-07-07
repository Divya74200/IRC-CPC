import socket
import threading
import rsa
from cryptography.fernet import Fernet
import json
import os
import time

#Global variables:
PORT = 45678
clientList = []
nicknameList = []
SERVICE_TYPE = "_chat._tcp.local."
SERVICE_NAME = "LocalChat._chat._tcp.local."
logFile = "chats.log"

#fernet_key = Fernet.generate_key()
fernetKey = b'Pu3bL3Y046StIOzkEAXmzyX9LEUk4DblnPRTkaBKdOY='
fernet = Fernet(fernetKey)

def serialize(obj):
    return json.dumps(obj).encode()

def deserialize(data):
    return json.loads(data.decode())

#Funcion to log the messages in the log file
def logMessage(msg):
    with open(logFile, "a", encoding="utf-8") as f:
        f.write(msg + "\n")

#Function to load previous messages from the chat log file
def loadPreviousMessages():
    if os.path.exists(logFile):
        with open(logFile, 'r') as f:
            return f.read()
    return ""

# Function to load current time stamps
def getTimeStamp():
    return time.strftime("[%Y-%m-%d %H:%M:%S]")

# Fuction to extact our ip
def getIp():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    finally:
        s.close()

# Function if any client causes any error, it will be removed the announced to the chat
def errorClient(client):
    if client in clientList:
        index = clientList.index(client)
        nickname = nicknameList[index]
        clientList.remove(client)
        nicknameList.remove(nickname)
        client.close()
        sendMessage(f"{nickname} left the chat")

#Function will greet the incomming connection and ask for their nickname
#Append that nickname to the list
# def receiveConnection(server):
#     client, addr = server.accept()
#     print(f"Connected with {str(addr)}")
#     client.send("Please enter your nickname : ".encode("utf-8"))
#     nickname = client.recv(1024).decode("utf-8").strip()
#     nicknameList.append(nickname)
#     clientList.append(client)
#     print(f"{nickname} joined from {addr}")
#     print(f"The choosen nickaname is {nickname}")
#     sendMessage(f"{getTimeStamp()} {nickname} joined the chat")

    

#Function will send the message to the users encoded
def sendMessage(msg):
    encoMessage = fernet.encrypt(serialize(msg)) + b'\n'
    for client in clientList:
        try:
            client.send(encoMessage)
        except:
            errorClient(client)
            

def handleClient(client):
    while True:
        try:
            msg = client.recv(1024)
            if msg:
                decrypted = deserialize(fernet.decrypt(msg))
                nickname = nicknameList[clientList.index(client)]
                fullMessage = f"{getTimeStamp()} {nickname} : {decrypted}"
                print(fullMessage)
                logMessage(fullMessage)
                sendMessage(fullMessage)
        except:
            errorClient(client)
            break


def peerHandler(client, nickname) :
    while True:
        try:
            message = input()
            fullMessage = f"{getTimeStamp()} {nickname} : {message}"
            if client:
                encrypted = fernet.encrypt(serialize(message))
                client.send(encrypted)
            else:
                sendMessage(fullMessage)
            logMessage(fullMessage)
        except Exception as e:
            print(f"Error: {e}")
            client.close()
            break

#User will face this thing first
print('''Iniitate into chat room as:
    1. Server (1)
    2. Clinet (2)''')

choice = input("Enter your choice : ")

if choice == "1":

    print("Starting server...")
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((getIp(),PORT))
    server.listen()
    print(f"Listenting on port {getIp()}:{PORT}")

    print("\n--- Previous Chat Logs ---")
    print(loadPreviousMessages())


    my_nickname = "actingServer"
    threading.Thread(target=peerHandler, args=(None, my_nickname)).start()

    while True:
        try:
           client, addr = server.accept()
           print(f"Connected with {str(addr)}")
           client.send("Please enter your nickname : ".encode("utf-8"))
           nickname = client.recv(1024).decode("utf-8")
           nicknameList.append(nickname)
           clientList.append(client)
           print(f"{nickname} joined from {addr}")
           print(f"The choosen nickaname is {nickname}")
           sendMessage(f"{getTimeStamp()} {nickname} joined the chat")
           thread = threading.Thread(target=handleClient, args=(client,))
           thread.start()

        except Exception as e :
            errorClient()
        except KeyboardInterrupt:
            print("Shutting down server...")
            server.close()


elif choice == "2":
    serverIp = input("Please enter server IP to Join : ")
    print("Searching for a server to join...")
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((serverIp, PORT))


    response = client.recv(1024).decode("utf-8")
    print(response)
    nickname = input("Enter your nickname: ")
    client.send(nickname.encode("utf-8"))

    print("\n--- Previous Chat Logs ---")
    print(loadPreviousMessages())

    def receive():
        while True:
            try:
                data = client.recv(1024)
                if data:
                    decrypted = deserialize(fernet.decrypt(data))
                    print(decrypted)
                    logMessage(decrypted)
            except:
                print("Disconnected from server.")
                break

    threading.Thread(target=receive, daemon=True).start()
    peerHandler(client, nickname)

else:
    exit()




#Update so far, code is working. Not crashing 
#After asking for nickname, i cannot send any messages
