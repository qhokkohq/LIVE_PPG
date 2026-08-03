from pathlib import Path
import time

def create_timestamp() -> str:
    return time.strftime("%Y%m%d_%H%M%S")


def create_plot_title(timestamp: str) -> str:
    return f"PPG_{timestamp}"


def create_csv_filepath(output_dir: str, timestamp: str) -> Path:
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)

    return output_dir / f"ppg_{timestamp}.csv"