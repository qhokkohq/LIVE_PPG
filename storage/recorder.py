from pathlib import Path
import pandas as pd
from dataclasses import asdict
from functools import singledispatchmethod

from communication.packets import DataPacket, FilteredPacket, SpO2Packet


class Recorder:

    def __init__(self):
        self.raw_packets: list[DataPacket] = []
        self.filtered_packets: list[FilteredPacket] = []
        self.spo2_packets: list[SpO2Packet] = []

    def clear(self):
        self.raw_packets.clear()
        self.filtered_packets.clear()
        self.spo2_packets.clear()

    @singledispatchmethod
    def append(self, obj):
        raise TypeError(type(obj))

    @append.register
    def _(self, packet: DataPacket):
        self.raw_packets.append(packet)

    @append.register
    def _(self, packet: FilteredPacket):
        self.filtered_packets.append(packet)

    @append.register
    def _(self, packet: SpO2Packet):
        self.spo2_packets.append(packet)

    def save(self, filepath):
        if not self.raw_packets:
            print("No data was collected. Skipping CSV export.")
            return False

        raw_file = self.create_specialised_filepath(Path(filepath), 'raw')
        filtered_file = self.create_specialised_filepath(Path(filepath), 'filtered')
        spo2_file = self.create_specialised_filepath(Path(filepath), 'spo2')

        print(f"Saving {len(self.raw_packets)} samples to {raw_file}...")
        self.save_dataclass_list(raw_file, self.raw_packets)

        print(f"Saving {len(self.filtered_packets)} samples to {filtered_file}...")
        self.save_dataclass_list(filtered_file, self.filtered_packets)

        print(f"Saving {len(self.spo2_packets)} samples to {spo2_file}...")
        self.save_dataclass_list(spo2_file, self.spo2_packets)

        if self.raw_packets:
            t0 = self.raw_packets[0].time_red_us
            t1 = self.raw_packets[-1].time_red_us

            duration = (t1 - t0) / 1e6

            print("Total duration (s):", duration)
            print("Effective rate (Hz):", len(self.raw_packets) / duration)

        return True

    @staticmethod
    def save_dataclass_list(filename, data):
        df = pd.DataFrame(asdict(x) for x in data)
        df.to_csv(filename, index=False)

    @staticmethod
    def create_specialised_filepath(filepath, string):
        new_stem = filepath.stem + '_' + string
        new_filepath = filepath.parent / new_stem
        return new_filepath.with_suffix('.csv')
