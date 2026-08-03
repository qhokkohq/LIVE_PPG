from dataclasses import dataclass
import numpy as np

@dataclass(slots=True)
class TimeSeries:
    t: np.ndarray
    v: np.ndarray

    def __post_init__(self):
        self.t = np.asarray(self.t)
        self.v = np.asarray(self.v)

    def __len__(self):
        return len(self.t)

    def __getitem__(self, idx):
        return TimeSeries(self.t[idx], self.v[idx])

    @property
    def dt(self):
        return np.mean(np.diff(self.t))

    @property
    def fs(self):
        return 1.0 / self.dt

    # def time_mask(self, t_start, t_end):
    #     mask = (self.t >= t_start) & (self.t <= t_end)
    #     return self[mask]

    # def zero_time(self, t0=None):
    #     if t0 is None:
    #         t0 = self.t[0]
    #     return TimeSeries(self.t - t0, self.v)
