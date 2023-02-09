import os
import sys

from process import Process
from connect import *


def do_exit():
    PROC.close()
    iserver.close()
    cserver.close()
    os._exit(0)


def handle_input():
    while True:
        data = input().split()
        if len(data) == 0:
            print("Invalid command. Valid inputs are 'connect', 'snapshot', 'loss', 'token', or 'exit'.")
        elif data[0] == "exit":
            do_exit()
        elif data[0] == "connect":
            connect_outgoing(PROC)
        elif data[0] == "snapshot":
            print('Initiating Global Snapshot Protocol...')
            PROC.initiate_snapshot()
        elif data[0] == "loss":
            PROC.loss = True
        elif data[0] == "token":
            PROC.get_token()
        else:
            print("Invalid command. Valid inputs are 'connect', 'snapshot', 'loss', 'token', or 'exit'.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f'Usage: python {sys.argv[0]} <processId>')
        sys.exit()

    Log = LogUtilities()

    PID = processes[sys.argv[1]]
    PROC = Process(PID)

    # Connect to Client & Server Machines iserver 和 cserver 都是 a socket object
    iserver = connect_incoming(PROC)
    cserver = connect_channels(PROC)

    # Handle User Input
    handle_input()
    do_exit()
