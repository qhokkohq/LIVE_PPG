import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

from storage.recorder import Recorder
from ui.ppg_plot_peaks import plot_ppg
from processing.signal_processor import SignalProcessor
from processing.spo2_estimator import SpO2Estimator
from processing.analysis import analyse_ppg, spo2_formula
from communication.packets import DataPacket
from utils.utils import clean_raw_arduino_df


def live_process_csv(csv_path, fs=fs):
    """Run a raw CSV through the real-time processing pipeline."""

    raw_df = pd.read_csv(csv_path)

    recorder = Recorder()
    processor = SignalProcessor(fs=fs)
    estimator = SpO2Estimator(fs=fs)

    for row in raw_df.itertuples(index=False):

        packet = DataPacket(
            time_red_us=row.time_red_us,
            red=row.red,
            time_ir_us=row.time_ir_us,
            ir=row.ir,
        )

        recorder.append(packet)

        filtered = processor.update(packet)

        if filtered is None:
            continue

        recorder.append(filtered)

        result = estimator.update(packet)

        if result is None:
            continue

        curr_spo2_packet, _ = result

        if curr_spo2_packet is not None:
            recorder.append(curr_spo2_packet)

    _, spo2_df = recorder.save(csv_path, save_raw=False)

    return raw_df, spo2_df


# ============================================================
# File loading
# ============================================================

def find_file(data_folder, suffix):
    """Find a single file with the given suffix. (raw, BUZUD, spo2)"""

    matches = list(data_folder.glob(f"*{suffix}"))

    if not matches:
        raise FileNotFoundError(
            f"No file matching '*{suffix}' found in {data_folder}"
        )

    if len(matches) > 1:
        raise RuntimeError(
            f"Multiple files matching '*{suffix}' found in {data_folder}"
        )

    return matches[0]


def load_data(data_folder, fs=fs, mode="cleaned", with_buzud=True):
    """Load either cleaned data or process raw data."""

    if mode == "cleaned":

        raw_df = pd.read_csv(find_file(data_folder, "_cleaned.csv"))

        spo2_df = pd.read_csv(find_file(data_folder, "_cleanedspo2.csv"))

        if with_buzud:
            buzud_df = pd.read_csv(find_file(data_folder, "_cleanedBUZUD.csv"))
        else:
            buzud_df = None

    else:

        raw_path = find_file(data_folder, "_raw.csv")

        raw_df, spo2_df = live_process_csv(raw_path, fs=fs)

        raw_df = clean_raw_arduino_df(raw_df)

        if with_buzud:
            buzud_df = pd.read_csv(find_file(data_folder, "_BUZUD.csv"))
        else:
            buzud_df = None

    return raw_df, spo2_df, buzud_df


def align_data(raw_df, spo2_df, buzud_df):
    """Align BUZUD and SpO2 by their final timestamps."""

    if buzud_df is None:
        return raw_df, spo2_df, None

    # BUZUD is sampled once per second
    buzud_df["t"] = np.arange(len(buzud_df), dtype=float)

    # Align the LAST BUZUD sample with the LAST SpO2 sample
    spo2_end = spo2_df["t"].iloc[-1]
    buzud_end = buzud_df["t"].iloc[-1]

    # Shift BUZUD so both endpoints are identical
    buzud_shift = spo2_end - buzud_end
    buzud_df["t"] += buzud_shift
    
    # Find the beginning of the overlapping region
    start_time = max(spo2_df["t"].iloc[0], buzud_df["t"].iloc[0])

    # Shift everything so the common start is t = 0
    raw_df["t_red"] -= start_time
    raw_df["t_ir"] -= start_time
    spo2_df["t"] -= start_time
    buzud_df["t"] -= start_time
    
    # Remove excess data before the common start
    raw_df = (raw_df[raw_df["t_red"] >= 0].reset_index(drop=True))
    spo2_df = (spo2_df[spo2_df["t"] >= 0].reset_index(drop=True))
    buzud_df = (buzud_df[buzud_df["t"] >= 0].reset_index(drop=True))

    return raw_df, spo2_df, buzud_df




def save_clean_csv(folder, raw_df, spo2_df, buzud_df=None):
    """Save processed data."""

    timestamp = folder.stem

    raw_df.to_csv(folder / f"{timestamp}_cleaned.csv", index=False)
    spo2_df.to_csv(folder / f"{timestamp}_cleanedspo2.csv", index=False)

    if buzud_df is not None:
        buzud_df.to_csv(folder / f"{timestamp}_cleanedBUZUD.csv", index=False)


# ============================================================
# Plotting
# ============================================================

def plot_measurement(data_folder, fs, raw_df, spo2_df, buzud_df=None):
    """Plot PPG and SpO2 results."""

    red_ppg = analyse_ppg(raw_df["t_red"], raw_df["red"], fs=fs)

    ir_ppg = analyse_ppg(raw_df["t_ir"], raw_df["ir"], fs=fs)

    spo2_column = f"spo2"

    spo2_df[spo2_column] = spo2_df["R"].apply(spo2_formula)

    # Trailing 8-sample mean
    rolling_mean = (spo2_df[spo2_column].rolling(window=8).mean())

    # Plot
    fig, axs = plt.subplots(3, 1, figsize=(12, 7), sharex=True)
    
    # RED
    plot_ppg(red_ppg, ax_signal=axs[0], label="660nm", color="red", plot_peaks=True)
    axs[0].set_title(data_folder.stem)

    # IR
    plot_ppg(ir_ppg, ax_signal=axs[1], label="880nm", color="black", plot_peaks=True)

    # SpO2
    axs[2].plot(spo2_df["t"], spo2_df[spo2_column], label=f"SpO2 calibrated")
    axs[2].plot(spo2_df["t"], rolling_mean, label="8 s rolling mean")

    if buzud_df is not None:
        axs[2].plot(buzud_df["t"], buzud_df["SpO2"], color="blue", label="BUZUD SpO2")

    axs[2].set_ylabel("Calculated SpO2 (%)")
    axs[2].set_xlim(left=0)
    axs[2].legend()
    axs[2].grid(True)

    fig.tight_layout()

    fig.savefig(data_folder / f"{data_folder.stem}.png")

    return fig


def main():
    WITH_BUZUD = True
    DATA_MODE = "cleaned"       # "cleaned" or "raw"

    big_folder = Path(r"C:\BORING\RESEARCH\MEASUREMENTS\NEW DATA 2026\LIVE_PPG\RAW_DATA_AUG_04_11_BREATHHOLD")
    fs = 50

    for data_folder in big_folder.iterdir():

        if not data_folder.is_dir():
            continue

        raw_df, spo2_df, buzud_df = load_data(data_folder, fs=fs, mode=DATA_MODE, with_buzud=WITH_BUZUD)

        if WITH_BUZUD:
            raw_df, spo2_df, buzud_df = align_data(raw_df, spo2_df, buzud_df)

        save_clean_csv(data_folder, raw_df, spo2_df, buzud_df)

        plot_measurement(data_folder, fs, raw_df, spo2_df, buzud_df)

    plt.show()


if __name__ == "__main__":
    main()