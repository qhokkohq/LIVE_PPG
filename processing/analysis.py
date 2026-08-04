from scipy.signal import find_peaks
import numpy as np

from models.time_series import TimeSeries
from models.ppg_data import PPGData


def analyse_ppg(time, i_full, i_ac):
    # DETECT PEAKS
    signal_data = TimeSeries(time, i_full)

    peaks_idx = get_peak_indices(i_ac, time)
    valleys_idx = get_peak_indices(-i_ac, time)

    if len(peaks_idx) < 2 or len(valleys_idx) < 2:
        return None

    peak_data = TimeSeries(time[peaks_idx], i_full[peaks_idx])
    valley_data = TimeSeries(time[valleys_idx], i_full[valleys_idx])

    # straight line between peaks, find interpolated peak at valley time
    interp_data = interpolate_peaks(valley_data.t, peak_data)

    if len(interp_data.t) == 0:
        return None

    interp_data, valley_data = validate_interp_pairs(interp_data, valley_data)

    # Find AC/DC at valley times
    acdc_data = calculate_acdc(interp_data.v, valley_data.v, valley_data.t)

    ppg_data = PPGData(signal_data, peak_data, valley_data, interp_data, acdc_data, "ppg")

    return ppg_data


def calculate_acdc(peak, valley, time):
    ac = peak - valley
    dc = valley
    acdc = ac / dc
    return TimeSeries(time, acdc)


def interpolate_peaks(interp_t, data):
    if len(data) == 0:
        return TimeSeries([], [])

    interp_v = np.interp(
        interp_t,
        data.t,
        data.v,
        left=np.nan,
        right=np.nan,
    )

    return TimeSeries(interp_t, interp_v)


def validate_interp_pairs(interp_data, valley_data):
    # Remove NaNs (outside interpolation range)
    valid = ~np.isnan(interp_data.v)

    interp_data = interp_data[valid]
    valley_data = valley_data[valid]

    return interp_data, valley_data


def get_peak_indices(v_ac, time):
    dt = np.mean(np.diff(time))

    # distance between samples
    max_hr = 180  # heart rate
    distance_sec = 60 / max_hr
    distance_samples = int(distance_sec / dt)

    # width of each sample
    peakwidth_sec = 0.12
    width_samples = peakwidth_sec / dt

    # prominence
    prom = 0.75 * np.std(v_ac)

    # Peaks
    peaks_idx, _ = find_peaks(
        v_ac,
        distance=distance_samples,
        width=width_samples,
        prominence=prom
    )

    return peaks_idx


def spo2_formula(acdc1, acdc2, l_ratio=None, eps_data='zij'):
    wl1 = 660
    wl2 = 880

    if eps_data == 'zij':
        # zijlstra
        # https://www.semanticscholar.org/paper/Absorption-spectra-of-human-fetal-and-adult-and-Zijlstra-Buursma/8ab210dc104c4330ad4b2c20882bca05be12760f
        # Table 2. Mlllimoiar Absorptlvltles (L . mmor’ . cm’) of Four Hemoglobin Derivatives of HbF and HbA at Selected Wavelengths In the Visible and Near-Infrared Spectral Range 
        eO1 = 0.08
        eO2 = 0.28
        eD1 = 0.81 
        eD2 = 0.20
        
    elif eps_data == 'prahl':
        # prahl: https://omlc.org/spectra/hemoglobin/summary.html
        eO1 = 319.6
        eO2 = 1154.0
        eD1 = 3226.56
        eD2 = 726.44
    
    else:
        print("Error choosing extinction coefficients. 'zij' or 'prahl'.")

    
    if l_ratio is None:
        # https://www.spiedigitallibrary.org/journals/journal-of-biomedical-optics/volume-23/issue-7/075005/Investigating-optical-path-and-differential-pathlength-factor-in-reflectance-photoplethysmography/10.1117/1.JBO.23.7.075005.pdf
        # dpf for 6mm 660nm 880nm
        dpf1 = 7.487
        dpf2 = 5.337    
        l_ratio = dpf2 / dpf1 # 0.7128
    
    R = acdc1 / acdc2
    a = eD1
    b = - l_ratio * eD2
    c = eD1 - eO1
    d = l_ratio * (eO2 - eD2)
    spo2 = (a + b * R) / (c + d * R) * 100
    return spo2

# # https://www.spiedigitallibrary.org/journals/journal-of-biomedical-optics/volume-23/issue-7/075005/Investigating-optical-path-and-differential-pathlength-factor-in-reflectance-photoplethysmography/10.1117/1.JBO.23.7.075005.pdf
# def calculate_spo2(acdc1, acdc2, wl1=660, wl2=880, dpf1=7.487, dpf2=5.337):

#     eO1, eO2, eD1, eD2 = get_extinction_coeff(wl1, wl2)
#     R = acdc1 / acdc2
#     a = eD1
#     l_ratio = dpf2 / dpf1
#     b = - l_ratio * eD2
#     c = eD1 - eO1
#     d = l_ratio * (eO2 - eD2)
#     spo2 = (a + b * R) / (c + d * R) * 100
#     return spo2

# # https://omlc.org/spectra/hemoglobin/summary.html
# def get_extinction_coeff(wl1, wl2):
#     tsv_file = r"C:\BORING\RESEARCH\MEASUREMENTS\NEW DATA 2026\Prahl absorption coeffs\lambda Hb02 Hb.tsv"

#     df = pd.read_csv(tsv_file, sep='\t')

#     wavelengths = df['lambda'].to_numpy()
#     hbO2 = df['Hb02'].to_numpy()
#     hb = df['Hb'].to_numpy()

#     # handles case where wl1 or wl2 is odd (we only have even wl data)
#     eO1 = np.interp(wl1, wavelengths, hbO2)
#     eO2 = np.interp(wl2, wavelengths, hbO2)

#     eD1 = np.interp(wl1, wavelengths, hb)
#     eD2 = np.interp(wl2, wavelengths, hb)

#     # print(f'eO1 {eO1}')
#     # print(f'eO2 {eO2}')
#     # print(f'eD1 {eD1}')
#     # print(f'eD2 {eD2}')

#     return eO1, eO2, eD1, eD2
