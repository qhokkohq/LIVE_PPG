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
BAUD_RATE = 115200
SAMPLE_FREQ = 50
TIME_WINDOW = 60
OUTPUT_DIR = 'captured data'

EPS_DATA = 'zij' # 'prahl'
L_RATIO = None

# MODE = 'REPLAY'
MODE = 'LIVE'

REPLAY_CSV = Path(r"C:\BORING\RESEARCH\MEASUREMENTS\NEW DATA 2026\PYTHON\captured_data\ppg_raw_20260730_171457.csv")

def main():

    if MODE == 'LIVE':
        data_source = SerialManager(SERIAL_PORT, BAUD_RATE)
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        title = f"PPG_{timestamp}"
        filepath = f'{OUTPUT_DIR}/PPG_{timestamp}.csv'
    else:
        data_source = ReplayManager(REPLAY_CSV, realtime=False)
        title = REPLAY_CSV.stem
        filepath = f'{OUTPUT_DIR}/{title}.csv'

    recorder = Recorder()

    live_data = LiveData(fs=SAMPLE_FREQ, window_seconds=TIME_WINDOW)

    processor = SignalProcessor(fs=SAMPLE_FREQ)

    estimator = SpO2Estimator(fs=SAMPLE_FREQ, l_ratio=L_RATIO, eps_data=EPS_DATA)

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
        estimator=estimator,
    )

    try:
        plotter.run()

    finally:
        recorder.save(filepath, l_ratio=L_RATIO, eps_data=EPS_DATA)
        data_source.close()


if __name__ == "__main__":
    main()