from matplotlib.ticker import MultipleLocator
import matplotlib.pyplot as plt
import numpy as np 

'''
# Plot simple PPG (only 1 waveform, no AC/DC)
fig, axs = plt.subplots(1, 1, figsize=(14, 8))
plot_ppg(ppg1, ax_signal=axs)
def plot_ppg(ppg, ax_signal, color, plot_peaks=False, plot_interp=False):

# Plot 1 PPG only, with AC/DC
fig, axs = plt.subplots(2, 1, figsize=(14, 8), sharex='col')
plot_ppg(ppg1, ax_signal=axs[0], ax_acdc=axs[1])

# Plot 2 PPGs with AC/DC
fig, axs = plt.subplots(2, 2, figsize=(14, 8), sharex='col')

plot_ppg(ppg1, ax_signal=axs[0, 0], ax_acdc=axs[1, 0])
plot_ppg(ppg2, ax_signal=axs[0, 1], ax_acdc=axs[1, 1])

'''
def plot_ppg(ppg, ax_signal, label, color, plot_peaks=False, plot_interp=False):

    # Signal plot
    ax_signal.plot(ppg.signal.t, ppg.signal.v, color=color, linewidth=1.2, label=label)
    
    if plot_peaks:
        ax_signal.plot(ppg.peaks.t, ppg.peaks.v, 'bo', markersize=2)
        ax_signal.plot(ppg.valleys.t, ppg.valleys.v, 'go', markersize=2)

    if plot_peaks and plot_interp:
        ax_signal.plot(ppg.peaks.t, ppg.peaks.v, 'rx', markersize=6, label='Systolic peak')
        ax_signal.plot(ppg.valleys.t, ppg.valleys.v, 'go', markersize=3, label='Valley')
        
        ax_signal.plot(ppg.peaks.t, ppg.peaks.v, 'r--', linewidth=1, label='Interpolation envelope')
        ax_signal.plot(ppg.interp.t, ppg.interp.v, 'mo', markersize=3, label='Interpolated peak')

    ax_signal.legend()
        
    ax_signal.set_ylabel('ADC Counts')
    
    ax_signal.set_xlabel('Time (s)')
    ax_signal.grid(True)
        