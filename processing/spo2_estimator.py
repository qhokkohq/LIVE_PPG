from collections import deque
import numpy as np

from communication.packets import FilteredPacket, SpO2Packet
from processing.analysis import analyse_ppg, spo2_formula


class SpO2Estimator:
    """
    Real-time SpO2 estimator.

    - Accepts one filtered Red/IR sample at a time.
    - Every second, analyses the previous 6/8/12 seconds.
    - Returns one SpO2 estimate (or None if insufficient data).
    
    - maintains a deque of recent SpO2 estimates of the past 8 seconds
    - every second, calculate a new SpO2 for the past 8 seconds of PPG signal
    - displayed value is an average of the 8 recent estimates
    """

    def __init__(self, fs):

        self.fs = fs

        # Maximum analysis window (12 s)
        self.max_window = 12
        max_samples = int(self.max_window * fs)

        self.filtered = deque(maxlen=max_samples) 
        self.spo2_history = deque(maxlen=8)
        
        self.last_update = 0.0
        self.current_hr = 75.0
        self.current_spo2 = None
        self.display_spo2 = None

    def reset(self):
        self.filtered.clear()
        self.spo2_history.clear()
        self.last_update = 0.0
        self.current_hr = 75.0
        self.current_spo2 = None
        self.display_spo2 = None
        

    def update(self, packet: FilteredPacket):

        self.filtered.append(packet)

        t = packet.t_red

        if t - self.last_update < 1.0:
            return None

        self.last_update = t

        if self.current_hr < 60:
            window = 12
        elif self.current_hr <= 120:
            window = 8
        else:
            window = 6

        samples = int(window * self.fs)

        if len(self.filtered) < samples:
            return None

        window_packets = list(self.filtered)[-samples:]

        spo2_v = self._calculate_window(window_packets)

        if spo2_v is not None:
            self.current_spo2 = spo2_v
            self.spo2_history.append(spo2_v)
            self.display_spo2 = np.mean(self.spo2_history)
            curr_spo2_packet = SpO2Packet(t=window_packets[-1].t_red, v=self.current_spo2)
            display_spo2_packet = SpO2Packet(t=window_packets[-1].t_red, v=self.display_spo2)
            return curr_spo2_packet, display_spo2_packet
            # return curr_spo2_packet

        return None

    def _calculate_window(self, packets: list[FilteredPacket]):

        t_red = np.array([p.t_red for p in packets])
        red_full = np.array([p.red_full for p in packets])
        red_ac = np.array([p.red_ac for p in packets])

        t_ir = np.array([p.t_ir for p in packets])
        ir_full = np.array([p.ir_full for p in packets])
        ir_ac = np.array([p.ir_ac for p in packets])

        red_ppg = analyse_ppg(t_red, red_full, red_ac)
        if red_ppg is None:
            return None

        if len(red_ppg.acdc.t) < 1:
            return None

        ir_ppg = analyse_ppg(t_ir, ir_full, ir_ac)

        if ir_ppg is None:
            return None

        if len(ir_ppg.acdc.t) < 1:
            return None

        acdc_red = np.mean(red_ppg.acdc.v)
        acdc_ir = np.mean(ir_ppg.acdc.v)
        spo2_v = spo2_formula(acdc_red, acdc_ir)

        if len(red_ppg.peaks.t) >= 2:
            ibi = np.mean(np.diff(red_ppg.peaks.t))
            self.current_hr = 60.0 / ibi

        return spo2_v
