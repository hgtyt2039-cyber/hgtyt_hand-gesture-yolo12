import socket

HOST = "127.0.0.1"
PORT = 8052

while True:
    cmd = input("Command: ")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, PORT))
    s.sendall(cmd.encode())
    s.close()
