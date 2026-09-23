from offline_analysis_buzud import load_data, live_process_csv

WITH_BUZUD = True
DATA_MODE = "cleaned"       # "cleaned" or "raw"

RAW_DATA_DIR = Path(r"C:\BORING\RESEARCH\MEASUREMENTS\NEW DATA 2026\LIVE_PPG\captured data")

SAMPLE_FREQ = 50
L_RATIO = 0.7128
EPS_DATA = "zij"


def main():
    for data_folder in RAW_DATA_DIR.iterdir():

        if not data_folder.is_dir():
            continue

        raw_df, spo2_df, buzud_df = load_data(data_folder, mode=DATA_MODE, with_buzud=WITH_BUZUD)

        if WITH_BUZUD:
            raw_df, spo2_df, buzud_df = align_data(raw_df, spo2_df, buzud_df)

        save_clean_csv(data_folder, raw_df, spo2_df, buzud_df)

        plot_measurement(data_folder, raw_df, spo2_df, buzud_df)

    plt.show()
