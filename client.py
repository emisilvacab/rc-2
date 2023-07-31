import sys
import socket

format = 'utf-8'
port = sys.argv[2]
serverName = sys.argv[1]
address = (serverName, int(port))
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
op = sys.argv[3]
key = sys.argv[4]
msg = op + " " + key
if len(sys.argv) == 6:
    value = sys.argv[5]
    msg = msg + " " + value
conn = True

client.connect(address)


def send(msg):
    message = msg.encode(format)
    client.send(message)
    answer = client.recv(4096).decode(format)
    print(answer)


send(msg)
print("Connected. Puede ingresar más comandos o EXIT para salir")

while msg != 'EXIT':
    msg = input()
    send(msg)

client.close()