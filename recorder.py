import pickle
import sys
import time
import threading

from snapshot import *

DELAY = 3

'''snapshots数组中为 (llc, pid): Snapshot Object'''
class Recorder:
    def __init__(self, pid):
        self.pid = pid
        self.snapshots = {}
        self.sockets = [None] * 5  # Sockets for receiving snapshots 全连接网络
        self.mutex = threading.Lock()

    ''' Handles receiving local snapshot from other processes  全连接网络内 快照结果传输处理逻辑'''

    def update_snapshot(self, sock, index):
        self.sockets[index] = sock
        while True:
            try:
                data = pickle.loads(sock.recv(1024))
                time.sleep(DELAY)
                snapshot = self.snapshots[data['id']]
                snapshot.merge_snapshot_data(data)
                self._check_ready_state(data['id'])
            except EOFError:
                print(f"Disconnected from Client {index}")
                sock.close()
                self.sockets[index] = None
                sys.exit()
            except Exception as e:
                print(e)
        sock.close()
        self.sockets[index] = None

    '''
    Checks for snapshot ready state and sends or prints snapshot if ready.
    if 是自己发起的snapshot 则可以打印并结束了
    elif 是别人发起的snapshot 要传回去
    '''

    def _check_ready_state(self, snapshot_id):
        llc, pid = snapshot_id
        snapshot = self.snapshots[snapshot_id]
        if self.pid == pid and snapshot.get_global_ready_state():
            snapshot.print()
            self.snapshots.pop(snapshot.id)
        elif self.pid != pid and snapshot.get_local_ready_state():
            socket = self.sockets[pid]
            payload = snapshot.get_snapshot_data()
            socket.sendall(pickle.dumps(payload))
            self.snapshots.pop(snapshot.id)

    ''' Saves local state and starts recording incoming channels '''

    def create_snapshot(self, snapshot_id, pid, balance):
        snapshot = Snapshot(snapshot_id, pid)
        self.snapshots[snapshot.id] = snapshot
        # 这个client开始快照，update_process_state相当于记录状态
        snapshot.update_process_state(pid, balance)
        return snapshot

    ''' Update all current snapshots with incoming message '''

    def update_channels(self, src, dest, value, marker=False):
        self.mutex.acquire()
        for snapshot in self.snapshots.values():
            snapshot.update_channel_state(src, dest, value, marker)
        self.mutex.release()

    ''' Stop recording channel `src` for snapshot (llc, pid) '''

    def close_channel(self, snapshot_id, src):
        snapshot = self.snapshots[snapshot_id]
        snapshot.close_channel_state(src, self.pid)
        self._check_ready_state(snapshot_id)

    ''' Close sockets '''

    def close_sockets(self):
        for sock in self.sockets:
            if sock is not None:
                sock.close()
