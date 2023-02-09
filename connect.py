import pickle
import socket
import threading

from utility import *
from logutilities import *

''' Connect channels for relaying finished snapshot 两两链接不管之前的哪个DAG 端口号在5000上'''


def connect_channels(proc):
    # Listener thread
    def listen(server, proc):
        server.listen(32)
        while True:
            sock, addr = server.accept()
            pid = pickle.loads(sock.recv(1024))
            LogUtilities().info(f"SNAPSHOT: Connected to Client {processes[pid]}")
            threading.Thread(target=proc.recorder.update_snapshot,
                             args=(sock, pid)).start()

    # Connect to listener of other clients
    def connect(pid, proc):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((socket.gethostname(), 5000 + pid))
            sock.sendall(pickle.dumps(proc.pid))
            LogUtilities().info(f"SNAPSHOT: Connected to Client {processes[pid]}")
            threading.Thread(target=proc.recorder.update_snapshot,
                             args=(sock, pid)).start()
        except ConnectionRefusedError:
            LogUtilities().error(f"SNAPSHOT: Failed Connection to Client {processes[pid]}.")

    # Connection protocol
    server = socket.socket()
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((socket.gethostname(), 5000 + proc.pid))
    threading.Thread(target=listen, args=(server, proc)).start()
    # 1连0 2连0，1 3连0，1，2 4 连0，1，2，3
    for i in range(proc.pid):
        connect(i, proc)
    return server


''' Listen for incoming requests to process '''


def connect_incoming(proc):
    # Listener thread
    def listen(server, proc):
        server.listen(32)
        while True:
            sock, addr = server.accept()
            pid = pickle.loads(sock.recv(1024))
            LogUtilities().info(f"Connected to Incoming Client {processes[pid]}")
            threading.Thread(target=proc.handle_incoming,
                             args=(sock, pid)).start()

    # Connection Protocol
    server = socket.socket()
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((socket.gethostname(), 8000 + proc.pid))
    LogUtilities().info("Listening for Incoming Client Connections...")
    threading.Thread(target=listen, args=(server, proc)).start()
    return server


''' Connect to outgoing channels for process 连网络的一部分，链接出边'''


def connect_outgoing(proc):
    # Connect to listener
    def connect(pid, proc):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((socket.gethostname(), 8000 + pid))
            sock.sendall(pickle.dumps(proc.pid))
            LogUtilities().info(f"Connected to Outgoing Client {processes[pid]}")
            proc.handle_outgoing(sock, pid)
        except ConnectionRefusedError:
            LogUtilities().error(f"Failed Connection to Outgoing Client {processes[pid]}")

    for i in Network.outgoing(proc.pid):
        connect(i, proc)
