from communication.serial_manager import SerialManager
from communication.replay_manager import ReplayManager
from storage.recorder import Recorder

from ui.live_data import LiveData
from ui.plotter import Plotter
from processing.signal_processor import SignalProcessor
from processing.spo2_estimator import SpO2Estimator

from utils.utils import *
import time
import matplotlib
matplotlib.use("TkAgg")

SERIAL_PORT = "COM5"
BAUD_RATE = 500000
SAMPLE_FREQ = 50
TIME_WINDOW = 60
OUTPUT_DIR = 'captured data'

# MODE = 'REPLAY'
MODE = 'LIVE'

REPLAY_CSV = Path(r"C:\BORING\RESEARCH\MEASUREMENTS\NEW DATA 2026\PYTHON\captured_data\ppg_raw_20260730_171457.csv")

def main():

    if MODE == 'LIVE':
        serial = SerialManager(SERIAL_PORT, BAUD_RATE)
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        title = f"PPG_{timestamp}"
        filepath = f'{OUTPUT_DIR}/ppg_{timestamp}.csv'
    else:
        serial = ReplayManager(REPLAY_CSV, realtime=False)
        title = REPLAY_CSV.stem
        filepath = f'{OUTPUT_DIR}/{title}.csv'

    recorder = Recorder()

    live_data = LiveData(SAMPLE_FREQ, TIME_WINDOW)

    processor = SignalProcessor(SAMPLE_FREQ)

    estimator = SpO2Estimator(SAMPLE_FREQ)

    # Plotter
    plotter = Plotter(
        mode=MODE,
        title=title,
        output_dir=OUTPUT_DIR,
        time_window=TIME_WINDOW,
        processor=processor,
        serial_manager=serial,
        recorder=recorder,
        live_data=live_data,
        estimator=estimator,
    )

    try:
        plotter.run()

    finally:
        recorder.save(filepath)
        serial.close()


if __name__ == "__main__":
    main()