import socket
import threading
import time
import sys
import zlib

format = 'utf-8'
port = sys.argv[2] if sys.argv[2] else '6969'
serverName = sys.argv[1] if sys.argv[1] else '192.168.1.5'
address = (serverName, int(port))
signature = f'{serverName}:{port}'
signature = zlib.crc32(signature.encode(format))
DDB = {}
mutex = {}
servers = []
broadcastPort = 2022

mutex['server'] = threading.Lock()

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # crea el socket del server, es tcp
server.bind(address)


# Threaded
def discovery():
    dSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    dSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    dSocket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    dSocket.bind(('', broadcastPort))
    while True:
        data, addr = dSocket.recvfrom(1024)
        data = data.decode(format)
        data_parts = data.split()
        if data_parts[0] == 'ANNOUNCE' and len(data_parts) == 2 and addr[0] != serverName:
            serverIP = addr[0]
            serverPort = data_parts[1]
            newServerSignature = f'{serverIP}:{serverPort}'
            newServerSignature = zlib.crc32(newServerSignature.encode(format))
            mutex['server'].acquire()
            distribute = True
            for server in servers:
                if newServerSignature in server:
                    distribute = False
            if distribute:
                print(f'[DISCOVERING] {addr}')
                serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                serverSocket.connect((serverIP, int(serverPort)))
                newServer = (newServerSignature, serverSocket)
                servers.append(newServer)
                re_alloc_info(newServer)  # esta funcion debe enviarle a el nuevo socket todo lo que le pertenezca
            mutex['server'].release()


def broadcast(port):
    bSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    bSocket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    bSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    bSocket.bind(('', 0))
    data = f"ANNOUNCE {port}\n".encode(format)
    while True:
        print("[BROADCAST] Announcing...")
        bSocket.sendto(data, ('255.255.255.255', broadcastPort))
        time.sleep(30)


def start():
    server.listen()
    print(f"[LISTENING] Server is listening on {serverName}")
    while True:
        conn, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()
        print(f"[ACTIVE CONNECTIONS] {threading.active_count() - 2}")


# Utils

def re_alloc_info(newServer):
    serverSig = newServer[0]
    serverSocket = newServer[1]
    keys = DDB.keys()
    toErase = []
    for key in keys:
        mutex[key].acquire()
        keyCode = zlib.crc32(key.encode(format))
        otherSigDist = abs(keyCode - serverSig) #Distancia de key a otro servidor
        sigDist = abs(keyCode - signature) #Distancia de key a nuestro servidor
        if ((otherSigDist < sigDist) or ((otherSigDist == sigDist) and (serverSig < signature))):
            value = DDB[key]
            setMessage = f'SET {key} {value}'
            serverSocket.send(setMessage.encode(format))
            toErase.append(key)
        mutex[key].release()
    for key in toErase:
        del DDB[key]


def check_message(msg):
    msg_parts = msg.split()
    err = False
    err_msg = ''
    alphanum = True
    handledByDiffServer = False
    connected = True
    for msg in msg_parts:
        if not (msg.isalnum()):
            alphanum = False
    if alphanum:
        if len(msg_parts) > 1:
            match msg_parts[0]:
                case 'SET':
                    if len(msg_parts) != 3:
                        err = True
                        err_msg = 'Comando invalido.'
                case 'GET':
                    if len(msg_parts) != 2:
                        err = True
                        err_msg = 'Comando invalido.'
                case 'DEL':
                    if len(msg_parts) != 2:
                        err = True
                        err_msg = 'Comando invalido.'
                case _:
                    err = True
                    err_msg = 'Comando invalido.'
        elif (msg_parts[0] == 'EXIT'):
            err = True
            connected = False
            err_msg = 'Disconnected.'
        else:
            err = True
            err_msg = 'Porfavor escriba una instruccion'
    else:
        err = True
        err_msg = 'El formato aceptado es alphanumerico.'
    if err:
        return msg_parts, err, err_msg, (), handledByDiffServer, connected
    key = zlib.crc32(msg_parts[1].encode(format))
    least = abs(key - signature)
    newConn = {}
    mutex['server'].acquire()
    for server in servers:
        serverSignature = server[0]
        newLeast = abs(key - serverSignature)
        if newLeast == least:
            if serverSignature < signature:
                least = newLeast
                newConn = server
                handledByDiffServer = True
        elif newLeast < least:
            least = newLeast
            newConn = server
            handledByDiffServer = True
    mutex['server'].release()
    return msg_parts, err, err_msg, newConn, handledByDiffServer, connected


# Handlers

def handle_request(msgparts):
    key = msgparts[1]
    match msgparts[0]:
        case 'GET':
            if key in mutex:
                mtx = mutex[key]
                mtx.acquire()
                value = DDB.get(key)
                reply_msg = "OK " + value + "\n"
                mtx.release()
            else:
                reply_msg = "NO\n"
        case 'SET':
            value = msgparts[2]
            if key in mutex:
                mutex[key].acquire()
            else:
                mutex[key] = threading.Lock()
                mutex[key].acquire()
            DDB[key] = value
            mutex[key].release()
            reply_msg = "OK\n"
            print(reply_msg)
            print(DDB)
        case 'DEL':
            if key in mutex:
                mutex[key].acquire()
                del DDB[key]
                mtx = mutex.pop(key)
                mtx.release()
                reply_msg = "OK\n"
            else:
                reply_msg = "NO\n"
    return reply_msg


def handle_client(conn, addr):
    print(f"[NEW CONN] {addr} connected.")
    connected = True
    while connected:
        msg = conn.recv(4096).decode(format)
        msgparts, err, err_msg, newConn, handledByDiffServer, connected = check_message(msg)
        if not (err):
            if not (handledByDiffServer):
                reply_msg = handle_request(msgparts)
            else:
                reply_msg = handle_server(msg, newConn)
            conn.send(reply_msg.encode(format))
        else:
            conn.send(err_msg.encode(format))
    print(f"[{addr}] {msg}")
    conn.close()


def handle_server(msg, newConn):
    middleManSocket = newConn[1]
    mutex['server'].acquire()
    middleManSocket.send(msg.encode(format))
    reply_msg = middleManSocket.recv(4096).decode(format)
    mutex['server'].release()
    return reply_msg


print("[STARTING] Server is starting...")
print("[BROADCAST] Starting broadcast in [PORT] 2022")
broadcastThread = threading.Thread(target=broadcast, args=[port])
discoveryThread = threading.Thread(target=discovery, args=[])
broadcastThread.start()
discoveryThread.start()
start()
