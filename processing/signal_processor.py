from processing.real_time_filter import RealTimeFilter
from communication.packets import DataPacket, FilteredPacket

class SignalProcessor:

    def __init__(self, fs):
        self.red = RealTimeFilter(fs=fs)        
        self.ir = RealTimeFilter(fs=fs)

        self.session_start_timestamp = None

    def reset(self):
        self.red.reset()
        self.ir.reset()

        self.session_start_timestamp = None

    def update(self, packet: DataPacket) -> FilteredPacket:
        if self.session_start_timestamp is None:
            self.session_start_timestamp = packet.time_red_us / 1e6

        t_red = packet.time_red_us / 1e6 - self.session_start_timestamp
        t_ir = packet.time_ir_us / 1e6 - self.session_start_timestamp

        return FilteredPacket(
            t_red=t_red,
            red=self.red.update(packet.red),

            t_ir=t_ir,
            ir=self.ir.update(packet.ir),
        )