from pathlib import Path
import time
import pandas as pd 

def clean_raw_arduino_df(df):
    time0 = min(df["time_red_us"].iloc[0], df["time_ir_us"].iloc[0])
    df["t_red"] = (df["time_red_us"] - time0) / 1e6
    df["t_ir"] = (df["time_ir_us"] - time0) / 1e6

    df = df.drop(columns=['time_red_us'])
    df = df.drop(columns=['time_ir_us'])
    df = df[['t_red', 'red', 't_ir', 'ir']]
    return df

def create_timestamp() -> str:
    return time.strftime("%Y%m%d_%H%M%S")


def create_plot_title(timestamp: str) -> str:
    return f"PPG_{timestamp}"


def create_csv_filepath(output_dir: str, timestamp: str) -> Path:
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)

    return output_dir / f"ppg_{timestamp}.csv"