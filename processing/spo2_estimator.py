from collections import deque
import numpy as np

from communication.packets import DataPacket, SpO2Packet
from processing.analysis import analyse_ppg, spo2_formula

class SpO2Estimator:
    """
    Real-time SpO2 estimator.

    - Accepts one RAW Red/IR sample at a time.
    - Every second, analyses the previous 8 seconds.
    - Returns one SpO2 estimate (or None if insufficient data).
    
    - maintains a deque of recent SpO2 estimates of the past 8 seconds
    - every second, calculate a new SpO2 for the past 8 seconds of PPG signal
    - displayed value is an average of the 8 recent estimates
    """

    def __init__(self, fs):

        self.fs = fs
        self.session_start_timestamp = None

        self.window_sec = 8
        self.num_samples = int(self.window_sec * fs)

        self.raw = deque(maxlen=self.num_samples) 
        self.spo2_history = deque(maxlen=self.window_sec)
        self.R_history = deque(maxlen=self.window_sec)
        
        self.last_update = 0.0
        self.current_hr = 75.0
        
        self.current_R = None 
        self.display_R = None 
        
        self.current_spo2 = None
        self.display_spo2 = None
        

    def reset(self):
        self.session_start_timestamp = None
        self.raw.clear()
        self.spo2_history.clear()
        self.last_update = 0.0
        self.current_hr = 75.0
        self.current_spo2 = None
        self.display_spo2 = None
        self.current_R = None 
        self.display_R = None 


    def update(self, packet: DataPacket):
        if self.session_start_timestamp is None:
            self.session_start_timestamp = packet.time_red_us / 1e6

        t = packet.time_red_us / 1e6 - self.session_start_timestamp

        self.raw.append(packet)

        # calculate spo2 every second
        if t - self.last_update < 1.0:
            return None

        self.last_update = t

        self.raw.append(packet)

        window_packets = list(self.raw)[-self.num_samples:]
        t = window_packets[-1].time_red_us / 1e6 - self.session_start_timestamp

        result = self._calculate_window(window_packets)
        
        if result is None:
            return None

        spo2_v, spo2_R = result

        self.current_spo2 = spo2_v
        self.current_R = spo2_R 
        
        self.spo2_history.append(spo2_v)
        self.R_history.append(spo2_R)
        
        self.display_spo2 = np.mean(self.spo2_history)
        self.display_R = np.mean(self.R_history)
        
        curr_spo2_packet = SpO2Packet(t=t, v=self.current_spo2, R=self.current_R)
        display_spo2_packet = SpO2Packet(t=t, v=self.display_spo2, R=self.display_R)
        
        return curr_spo2_packet, display_spo2_packet


    def _calculate_window(self, packets: list[DataPacket]):

        t_red = np.array([p.time_red_us / 1e6 for p in packets])
        red = np.array([p.red for p in packets], dtype=float)

        t_ir = np.array([p.time_ir_us / 1e6 for p in packets])
        ir = np.array([p.ir for p in packets], dtype=float)

        # Remove absolute timestamp offset
        t_red -= t_red[0]
        t_ir -= t_ir[0]
        
        red_ppg = analyse_ppg(t_red, red, self.fs)
        
        if red_ppg is None:
            print('red ppg none', t_red[0])
            return None

        if len(red_ppg.acdc.t) < 1:
            print('red ppg none', t_red[0])
            return None
        
        ir_ppg = analyse_ppg(t_ir, ir, self.fs)
        
        if ir_ppg is None:
            print('ir ppg none', t_red[0])
            return None

        if len(ir_ppg.acdc.t) < 1:
            print('ir ppg none', t_red[0])
            return None

        acdc_red = np.mean(red_ppg.acdc.v)
        acdc_ir = np.mean(ir_ppg.acdc.v)
        spo2_R = acdc_red / acdc_ir
        spo2_v = spo2_formula(spo2_R)

        if len(red_ppg.peaks.t) >= 2:
            ibi = np.mean(np.diff(red_ppg.peaks.t))
            self.current_hr = 60.0 / ibi

        return spo2_v, spo2_R 
