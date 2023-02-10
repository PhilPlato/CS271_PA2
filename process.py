import random

from recorder import *
from utility import *

DELAY = 3
TOKEN_PASS = 1

'''每个client拥有一个process'''
''' Implement snapshot protocol for a single process '''


class Process:
    def __init__(self, pid):
        self.pid = pid
        self.llc = 0
        # balance在这里存储 也就是说有无token在这里存储 开始时都没有Token所以设为0
        self.balance = 0
        self.recorder = Recorder(pid)
        # outgoing 和 incoming数组存储DAG上的链接情况
        self.outgoing = [None] * 5
        self.incoming = [None] * 5
        self.loss = False

        self.log = LogUtilities()
        self.mutex = threading.Lock()

    ''' Thread for handling messages on incoming sockets
     这里的socket是accept以后那个新的socket index是起点的pid 终点自然是Process所在的client
     DAG网络
     在DAG网络上可能会收到什么消息
     1.TRANSFER 把Token 从一个client 传到另一个client 传输消息格式{ 'op' : 'TRANSFER', 'value' : 1 }
     2. { 'op' : 'MARKER', 'id' : snapshot_id }
         snapshot = self.recorder.create_snapshot(
      (self.llc, self.pid), self.pid, self.balance)

      create_snapshot(self, snapshot_id, pid, balance)

      也即 snapshot_id 为（llc, pid）
     '''

    def handle_incoming(self, sock, index):
        self.incoming[index] = sock
        while True:
            try:
                data = pickle.loads(sock.recv(1024))
                time.sleep(DELAY)
                self._update_llc()
                if data['op'] == 'MARKER':
                    id = data['id']
                    self.log.info(f"Received MARKER for Snapshot {(id[0], processes[id[1]])}")
                    if id in self.recorder.snapshots:
                        self.log.info(f"Second MARKER: Closing Channel {processes[index]} -> {processes[self.pid]}")
                        self.recorder.update_channels(index, self.pid, data, marker=True)
                        self.recorder.close_channel(id, index)
                    else:
                        self.log.info(f"First MARKER: Recording Channel {processes[index]} -> {processes[self.pid]}")
                        self.recorder.create_snapshot(id, self.pid, self.balance)
                        self.recorder.close_channel(id, index)
                        self.recorder.update_channels(index, self.pid, data, marker=True)
                        self._send_markers(id)
                elif data['op'] == "TRANSFER":
                    if self.loss == False or (self.loss == True and (random.random() < 0.9)):
                        value = data['value']
                        self._update_balance(value)
                        self.recorder.update_channels(index, self.pid, value)
                        self.log.info(f"Transfer: RECEIVED TOKEN FROM CLIENT {processes[index]}")
                        self.transfer_token()
            except EOFError:
                self.log.error(f"Disconnected from Client {processes[index]}")
                sock.close()
                self.incoming[index] = None
                sys.exit()
            except Exception as e:
                print(e)
        sock.close()
        self.incoming[index] = None

    ''' Updates Lamport Logical Clock Counter '''

    def _update_llc(self, value=None):
        self.mutex.acquire()
        if (value):
            self.llc = max(value, self.llc) + 1
        else:
            self.llc += 1
        self.mutex.release()

    ''' Sends markers to all outgoing connections'''

    def _send_markers(self, snapshot_id):
        payload = {'op': 'MARKER', 'id': snapshot_id}
        for sock in self.outgoing:
            if sock is not None:
                sock.sendall(pickle.dumps(payload))

    ''' Updates process balance'''

    def _update_balance(self, value):
        self.mutex.acquire()
        self.balance += value
        self.mutex.release()

    ''' Add socket to outgoing list '''

    def handle_outgoing(self, sock, index):
        self.outgoing[index] = sock

    ''' Initiate global snapshot protocol '''

    def initiate_snapshot(self):
        snapshot = self.recorder.create_snapshot(
            (self.llc, self.pid), self.pid, self.balance)
        self._send_markers(snapshot.id)

    def get_token(self):
        self.balance = 1
        self.transfer_token()

    def transfer_token(self):
        random_element = random.choice(Network.outgoing(self.pid))
        time.sleep(TOKEN_PASS)
        socket = self.outgoing[random_element]
        if socket is None:
            print("Transfer: NOT CONNECTED TO CLIENT")
            return
        payload = {'op': 'TRANSFER', 'value': 1}
        self._update_balance(-1)
        socket.sendall(pickle.dumps(payload))
        self.log.info(f"Transfer sent to Client {processes[random_element]}")

    ''' Close all sockets '''

    def close(self):
        for sock in self.incoming + self.outgoing:
            if sock is not None:
                sock.close()
        self.recorder.close_sockets()
