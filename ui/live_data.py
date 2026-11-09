from collections import deque
from functools import singledispatchmethod

from communication.packets import FilteredPacket, SpO2Packet

class LiveData:

    def __init__(self, fs, window_seconds):
        window_len = fs * window_seconds
        self.filtered_packets = deque(maxlen=window_len)
        self.spo2_packets = deque(maxlen=window_len)

    @singledispatchmethod
    def append(self, obj):
        raise TypeError(type(obj))

    @append.register
    def _(self, packet: FilteredPacket):
        self.filtered_packets.append(packet)

    @append.register
    def _(self, packet: SpO2Packet):
        self.spo2_packets.append(packet)

    def clear(self):
        self.filtered_packets.clear()
        self.spo2_packets.clear()

    @property
    def t_red(self):
        return [p.t_red for p in self.filtered_packets]

    @property
    def red(self):
        return [p.red for p in self.filtered_packets]

    @property
    def t_ir(self):
        return [p.t_ir for p in self.filtered_packets]

    @property
    def ir(self):
        return [p.ir for p in self.filtered_packets]

    @property
    def spo2_t(self):
        return [p.t for p in self.spo2_packets]

    @property
    def spo2_v(self):
        return [p.v for p in self.spo2_packets]