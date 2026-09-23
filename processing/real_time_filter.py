from scipy.signal import butter, lfilter, lfilter_zi
import numpy as np

class RealTimeFilter:
    b: np.ndarray
    a: np.ndarray
    zi: np.ndarray  # initial state of filter

    def __init__(self, mode, fs):
        order = 4
        fL = 0.4
        fH = 10
        if mode == 'lowpass':
            fc = fH
        else:
            fc = (fL, fH)

        self.b, self.a = butter(
            N=order,
            Wn=fc,
            btype=mode,
            fs=fs,
        )
        self.reset()

    def reset(self):
        self.zi = None

    def update(self, sample):

        if self.zi is None:
            # Initialize as if the input had always been 'sample'
            self.zi = lfilter_zi(self.b, self.a) * sample

        y, self.zi = lfilter(
            self.b,
            self.a,
            [sample],
            zi=self.zi,
        )

        return float(y[0])
