# Mapping letters to numbers for process IDs
A, B, C, D, E = 0, 1, 2, 3, 4

processes = {
    'A': A, 'B': B, 'C': C, 'D': D, 'E': E,
    A: 'A', B: 'B', C: 'C', D: 'D', E: 'E'
}


# Network Connections
class Network:
    incoming_network = {
        A: [B, D],
        B: [A, C, D, E],
        C: [D],
        D: [B, E],
        E: [D]
    }
    outgoing_network = {
        A: [B],
        B: [A, D],
        C: [B],
        D: [A, B, C, E],
        E: [B, D]
    }

    def incoming(pid):
        return Network.incoming_network[pid]

    def outgoing(pid):
        return Network.outgoing_network[pid]
