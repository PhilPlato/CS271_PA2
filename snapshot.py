from logutilities import LogUtilities
from utility import *

''' Object representing a snapshot for a single request 对每一个snapshot拥有一个Snapshot'''


class Snapshot:
    def __init__(self, snapshot_id, host_id):
        self.id = snapshot_id
        self.process_states = [None] * 5
        self.channel_states = {}
        self.log = LogUtilities()
        # 存储入边
        self.open_channels = Network.incoming(host_id).copy()

    ''' Updates process state with current balance 更新现在的balance是多少'''

    def update_process_state(self, pid, value):
        self.process_states[pid] = value

    ''' Prints formatted string for snapshot
  打印snapshot的情况， 可以看到process_states中存储每个节点上的balance情况，channel_states存储每个入边上的情况'''

    def print(self):
        print("---------------")
        print(f"Local States:\
        \n\tA: ${self.process_states[A]}\
        \n\tB: ${self.process_states[B]}\
        \n\tC: ${self.process_states[C]}\
        \n\tD: ${self.process_states[D]}\n"
              )
        print("Channel States")
        for src, dest in self.channel_states:
            print(f"\t{processes[src]} -> {processes[dest]}: {self.channel_states[src, dest]}")
        print("---------------")

    ''' Updates channel state with incoming messages '''

    def update_channel_state(self, src, dest, value, marker=False):
        if (src, dest) not in self.channel_states:
            self.channel_states[src, dest] = []
        if marker and value['id'] == self.id:
            return
        # python中数组可以直接相加起到拼接的作用。
        self.channel_states[src, dest] += [value]

    ''' Stops recording messages for channel open_channels是监听所有入边 如果某个边收到Marker了就remove 掉'''

    def close_channel_state(self, src, dest):
        if (src, dest) not in self.channel_states:
            self.channel_states[src, dest] = []
        self.open_channels.remove(src)

    ''' Returns true if snapshot is ready to sent to requester 入边收到了所有的Marker'''

    def get_local_ready_state(self):
        return len(self.open_channels) < 1

    ''' Returns true if snapshot is ready to print 自己snapshot照好了并且收到了从别人传来的本次快照情况'''

    def get_global_ready_state(self):
        return (None not in self.process_states and
                self.get_local_ready_state())

    ''' Returns sendable snapshot data '''

    def get_snapshot_data(self):
        return {
            "op": "MARKER",
            "id": self.id,
            "pr_state": self.process_states,
            "ch_state": self.channel_states
        }

    ''' Merges local snapshot data from other process '''

    def merge_snapshot_data(self, data):
        if data["id"] != self.id:
            self.log.info("not the same id, no update")
            return

        # Merge Process & Channel States
        pstate = data["pr_state"]
        self.process_states = [pstate[i] if pstate[i] is not None
                               else self.process_states[i] for i in range(5)]
        self.channel_states = data["ch_state"] | self.channel_states
