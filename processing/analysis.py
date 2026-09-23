from scipy.signal import find_peaks
import numpy as np

from models.time_series import TimeSeries
from models.ppg_data import PPGData

from scipy.signal import filtfilt, butter

def analyse_ppg(time, signal, fs):
    
    i_full = butter_ppg(signal, fs, 'lowpass')
    i_ac = butter_ppg(signal, fs, 'bandpass')
        
    # DETECT PEAKS
    signal_data = TimeSeries(time, i_full)

    peaks_idx = get_peak_indices(i_ac, time)
    valleys_idx = get_peak_indices(-i_ac, time)

    if len(peaks_idx) < 2 or len(valleys_idx) < 2:
        return None

    # cannot do this when using lfilt (causal)
    # this is ok when using filtfilt
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


def spo2_formula(R):
    # wl1 = 660
    # wl2 = 880
    
    # # prahl: https://omlc.org/spectra/hemoglobin/summary.html
    # eO1 = 319.6
    # eO2 = 1154.0
    # eD1 = 3226.56
    # eD2 = 726.44
        
    # # https://www.spiedigitallibrary.org/journals/journal-of-biomedical-optics/volume-23/issue-7/075005/Investigating-optical-path-and-differential-pathlength-factor-in-reflectance-photoplethysmography/10.1117/1.JBO.23.7.075005.pdf
    # dpf1 = 7.487
    # dpf2 = 5.337    
    # l_ratio = dpf2 / dpf1 # 0.7128
    
    # a = eD1
    # b = - l_ratio * eD2
    # c = eD1 - eO1
    # d = l_ratio * (eO2 - eD2)
    
    a = 3226.560000
    b = -417.398752
    c = 2952.348464
    d = 392.777540
    
    spo2 = (a + b * R) / (c + d * R) * 100
    return spo2


def butter_ppg(ppg, fs, option='lowpass'):
    order = 4 
    fL = 0.5 
    fH = 10 
    sm_win = 50 
    
    if option == 'lowpass':
        b, a = butter(order, fH, 'lowpass', fs=fs)
    else:
        b, a = butter(order, [fL, fH], 'bandpass', fs=fs)
        
    ppg_butter = filtfilt(b, a, ppg)
    
    if fs >= 75:
        # moving average smoothing filter
        win = round(fs * sm_win/1000)
        B = 1 / win * np.ones(win)
        ppg = filtfilt(B, 1, ppg_butter)
    else:
        ppg = ppg_butter
        
    return ppg
    