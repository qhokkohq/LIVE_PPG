from communication.serial_manager import SerialManager
from communication.replay_manager import ReplayManager
from storage.recorder import Recorder

from ui.live_data import LiveData
from ui.plotter import Plotter
from processing.signal_processor import SignalProcessor
from processing.spo2_estimator import SpO2Estimator
from processing.bp_estimator import BPEstimator
from communication.packets import DataPacket
import numpy as np
from utils.utils import *
import time
import matplotlib.pyplot as plt
import pandas as pd 
from pathlib import Path

# from offline_analysis import plot_saved_csv

import matplotlib
matplotlib.use("TkAgg")

SERIAL_PORT = "COM5"
BAUD_RATE = 115200
SAMPLE_FREQ = 100
TIME_WINDOW = 30
OUTPUT_DIR = r"C:\BORING\RESEARCH\MEASUREMENTS\NEW DATA 2026\BLOOD PRESSURE ESTIMATION\RAW DATA SEP 2026"
Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

sex = 'F'
age = 25 
height = 167 
weight = 57 
resting_hr = 66

MODE = 'REPLAY'
REPLAY_CSV = Path(r"C:\BORING\RESEARCH\MEASUREMENTS\NEW DATA 2026\LIVE_PPG\captured data\20260919_134037_raw.csv")

def main():
    if MODE == 'LIVE':
        save_raw = True
        data_source = SerialManager(SERIAL_PORT, BAUD_RATE)
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        title = f"{timestamp}"
        filepath = f'{OUTPUT_DIR}/{timestamp}_raw.csv'
    else:
        save_raw = False
        data_source = ReplayManager(REPLAY_CSV, realtime=False)
        title = REPLAY_CSV.stem
        filepath = f'{OUTPUT_DIR}/{title}.csv'
    

    recorder = Recorder()

    live_data = LiveData(fs=SAMPLE_FREQ, window_seconds=TIME_WINDOW)

    processor = SignalProcessor(fs=SAMPLE_FREQ)

    spo2_estimator = SpO2Estimator(fs=SAMPLE_FREQ)

    bp_estimator = BPEstimator(
        model_file=r"C:\BORING\RESEARCH\MEASUREMENTS\NEW DATA 2026\LIVE_PPG\models\model_weights.pth",
        scaler_file=r"C:\BORING\RESEARCH\MEASUREMENTS\NEW DATA 2026\LIVE_PPG\models\demographic_scaler.pkl",
        fs=SAMPLE_FREQ,
        sex=sex,
        age=age,
        height=height,
        weight=weight,
        resting_hr=resting_hr,
    )

    # Plotter
    plotter = Plotter(
        mode=MODE,
        title=title,
        output_dir=OUTPUT_DIR,
        time_window=TIME_WINDOW,
        processor=processor,
        data_source=data_source,
        recorder=recorder,
        live_data=live_data,
        spo2_estimator=spo2_estimator,
        bp_estimator=bp_estimator,
    )

    try:
        plotter.run()

    finally:
        raw_df, spo2_df = recorder.save(filepath, save_spo2=False, save_bp=False, save_raw=True)
        data_source.close()

if __name__ == "__main__":
    main()
