import struct
from dataclasses import dataclass

START_PACKET = 0xFA
DATA_PACKET = 0xAA
END_PACKET = 0xFB

DATA_STRUCT = struct.Struct("<IhIh")
TOTAL_DATA_SIZE = 1 + DATA_STRUCT.size


@dataclass(slots=True)
class DataPacket:
    time_red_us: int
    red: int
    time_ir_us: int
    ir: int

@dataclass(slots=True)
class FilteredPacket:
    t_red: float
    red: float
    t_ir: float
    ir: float

@dataclass(slots=True)
class SpO2Packet:
    t: float
    v: float
    R: float 
    
@dataclass(slots=True)
class BPPacket:
    t: float
    sbp: float
    dbp: float