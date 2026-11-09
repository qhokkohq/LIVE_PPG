from collections import deque

import joblib
import numpy as np
import torch

from processing.CNN_MLP_BP import CNN_MLP_BP
from communication.packets import DataPacket, BPPacket

from pathlib import Path 
import pandas as pd 
import numpy as np 
import matplotlib.pyplot as plt 
from scipy.signal import butter, cheby2, filtfilt, resample, sosfiltfilt
from scipy.stats import skew 
import math 

class BPEstimator:

    def __init__(self, model_file, scaler_file, fs,
        sex, age, height, weight, resting_hr):

        self.fs = fs

        # -------------------------
        # Model
        # -------------------------
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        self.model = CNN_MLP_BP(num_features=4, output_size=2).to(self.device)

        self.model.load_state_dict(torch.load(model_file, map_location=self.device, weights_only=True))

        self.model.eval()

        # -------------------------
        # Demographic scaler
        # -------------------------
        self.scaler = joblib.load(scaler_file)
        
        sexx = 0 if sex == 'M' else 1 
        
        bmi = weight / (height / 100)**2 
        self.features = np.array([[sexx, age, bmi, resting_hr]], dtype=np.float32)

        self.features_scaled = self.scaler.transform(self.features).astype(np.float32)

        # -------------------------
        # PPG buffer
        # -------------------------
        self.window_sec = 2.1
        self.num_samples = round(self.window_sec * fs)
        self.raw = deque(maxlen=round(math.ceil(self.window_sec) * self.fs)) # 3s

        self.current_sbp = None
        self.current_dbp = None
        
        self.samples_since_prediction = 0
        self.session_start_timestamp = None
        
    def update(self, packet: DataPacket):

        # Set start time from first packet
        if self.session_start_timestamp is None:
            self.session_start_timestamp = packet.time_red_us / 1e6

        # Time since recording started
        t = (packet.time_red_us / 1e6 - self.session_start_timestamp)

        # Add raw red PPG sample
        self.raw.append(packet.red)
        self.samples_since_prediction += 1

        # Need a complete 2.1 s window
        if len(self.raw) < self.num_samples:
            return None

        # Non-overlapping predictions
        if self.samples_since_prediction < self.num_samples:
            return None

        self.samples_since_prediction = 0

        ppg = np.asarray(self.raw, dtype=np.float32)

        return self._predict(ppg, t)
    
    def _predict(self, ppg, t):
        
        ppg = butter_ppg(ppg, fs=self.fs, option="bandpass")

        # Standardise individual segment
        mean = np.mean(ppg)
        std = np.std(ppg)

        if std < 1e-8:
            return None

        ppg = (ppg - mean) / std

        # --------------------------------
        # Tensor
        # --------------------------------

        ppg_tensor = torch.from_numpy(ppg.astype(np.float32))

        # (samples,) -> (1, 1, samples)
        ppg_tensor = (
            ppg_tensor
            .unsqueeze(0)
            .unsqueeze(0)
            .to(self.device)
        )

        features_tensor = torch.from_numpy(self.features_scaled).to(self.device)

        # --------------------------------
        # Prediction
        # --------------------------------

        with torch.inference_mode():

            prediction = self.model(ppg_tensor, features_tensor)

        self.current_sbp = prediction[0, 0].item()
        self.current_dbp = prediction[0, 1].item()

        return BPPacket(
            t=t,
            sbp=self.current_sbp,
            dbp=self.current_dbp
        )
    
    def reset(self):

        self.raw.clear()

        self.samples_since_prediction = 0
        self.session_start_timestamp = None

        self.current_sbp = None
        self.current_dbp = None
        
    


    

    

    def load_signal(ppg_file, fs=100):
        df = pd.read_csv(ppg_file)
        time, raw_signal = make_constant_fs_ppg(df['red'], df['time_red_us'], fs=fs)
        ppg = butter_filter(raw_signal, order=4, lower=0.5, upper=15, fs=fs)
        ppg = ppg * -1
        return time, ppg
    
    def _get_model_segment(self):

        packets = list(self.raw)

        time = np.array([p.time_red_us / 1e6 for p in packets])

        signal = np.array([p.red for p in packets], dtype=float)

        # Latest sample defines end of window
        end_time = time[-1]

        # We want exactly 210 points ending at latest time
        target_time = (end_time - (np.arange(210)[::-1] / self.fs))

        # Make sure buffer covers target interval
        if target_time[0] < time[0]:
            return None

        # makes ppg have constant fs
        ppg = np.interp(target_time, time, signal)

        return ppg
