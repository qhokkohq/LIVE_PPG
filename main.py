from communication.serial_manager import SerialManager
from storage.recorder import Recorder

from ui.live_data import LiveData
from ui.plotter import Plotter
from processing.signal_processor import SignalProcessor
from processing.spo2_estimator import SpO2Estimator
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
SAMPLE_FREQ = 200
TIME_WINDOW = 30
OUTPUT_DIR = r"C:\BORING\RESEARCH\MEASUREMENTS\NEW DATA 2026\BLOOD PRESSURE ESTIMATION\RAW DATA SEP 2026"
Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

MODE = 'LIVE'
def main():
    save_raw = True
    serial_manager = SerialManager(SERIAL_PORT, BAUD_RATE)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    title = f"{timestamp}"
    filepath = f'{OUTPUT_DIR}/{timestamp}_raw.csv'

    recorder = Recorder()

    live_data = LiveData(fs=SAMPLE_FREQ, window_seconds=TIME_WINDOW)

    processor = SignalProcessor(fs=SAMPLE_FREQ)

    estimator = SpO2Estimator(fs=SAMPLE_FREQ)

    # Plotter
    plotter = Plotter(
        mode=MODE,
        title=title,
        output_dir=OUTPUT_DIR,
        time_window=TIME_WINDOW,
        processor=processor,
        serial_manager=serial_manager,
        recorder=recorder,
        live_data=live_data,
        estimator=estimator,
    )

    try:
        plotter.run()

    finally:
        raw_df, spo2_df = recorder.save(filepath, save_spo2=False, save_raw=True)
        serial_manager.close()

if __name__ == "__main__":
    main()
