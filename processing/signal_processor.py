from processing.real_time_filter import RealTimeFilter
from communication.packets import DataPacket, FilteredPacket


class SignalProcessor:

    def __init__(self, fs):
        self.red_full = RealTimeFilter(mode="lowpass", fs=fs)
        self.red_ac = RealTimeFilter(mode="bandpass", fs=fs)

        self.ir_full = RealTimeFilter(mode="lowpass", fs=fs)
        self.ir_ac = RealTimeFilter(mode="bandpass", fs=fs)

        self.session_start_timestamp = None

    def reset(self):
        self.red_full.reset()
        self.red_ac.reset()

        self.ir_full.reset()
        self.ir_ac.reset()

        self.session_start_timestamp = None

    def update(self, packet: DataPacket) -> FilteredPacket:
        if self.session_start_timestamp is None:
            self.session_start_timestamp = packet.time_red_us / 1e6

        t_red = packet.time_red_us / 1e6 - self.session_start_timestamp
        t_ir = packet.time_ir_us / 1e6 - self.session_start_timestamp

        return FilteredPacket(
            t_red=t_red,
            red_full=self.red_full.update(packet.red),
            red_ac=self.red_ac.update(packet.red),

            t_ir=t_ir,
            ir_full=self.ir_full.update(packet.ir),
            ir_ac=self.ir_ac.update(packet.ir),
        )