from scipy.signal import butter, lfilter, lfilter_zi
from collections import deque
import numpy as np

# only used for plotting. not used for processing. 
# just a MOVING AVERAGE FILTER

class RealTimeFilter:

    def __init__(self, fs, window_ms=50):

        window_samples = round(fs * window_ms / 1000)

        self.buffer = deque(maxlen=window_samples)

    def reset(self):
        self.buffer.clear()

    def update(self, sample):

        self.buffer.append(sample)

        return np.mean(self.buffer)