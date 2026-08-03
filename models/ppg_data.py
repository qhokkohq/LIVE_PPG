from dataclasses import dataclass
from models.time_series import TimeSeries


@dataclass
class PPGData:
    signal: TimeSeries
    peaks: TimeSeries
    valleys: TimeSeries
    interp: TimeSeries  # "peaks" interpolated at valley times
    acdc: TimeSeries
    title: str

    def time_mask(self, t_start, t_end):
        return PPGData(
            signal=self.signal.time_mask(t_start, t_end),
            peaks=self.peaks.time_mask(t_start, t_end),
            valleys=self.valleys.time_mask(t_start, t_end),
            interp=self.interp.time_mask(t_start, t_end),
            acdc=self.acdc.time_mask(t_start, t_end),
            title=self.title,
        )

    def zero_time(self):
        t0 = self.signal.t[0]
        return PPGData(
            signal=self.signal.zero_time(t0),
            peaks=self.peaks.zero_time(t0),
            valleys=self.valleys.zero_time(t0),
            interp=self.interp.zero_time(t0),
            acdc=self.acdc.zero_time(t0),
            title=self.title,
        )