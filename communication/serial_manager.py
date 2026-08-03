import time
import serial
import threading
import queue

from communication.packets import (
    DataPacket,
    START_PACKET,
    DATA_PACKET,
    END_PACKET,
    DATA_STRUCT,
    TOTAL_DATA_SIZE,
)

START_CMD = b's'
STOP_CMD = b'q'


class SerialManager:

    def __init__(self, serial_port, baud_rate):

        self.ser = serial.Serial(
            serial_port,
            baud_rate,
            timeout=0.1,
        )

        time.sleep(2)
        self.ser.reset_input_buffer()

        self.data_packet_que = queue.Queue()

        self.running = False
        self.thread = None
        
    def clear_queue(self):

        count = 0

        while True:
            try:
                self.data_packet_que.get_nowait()
                count += 1
            except queue.Empty:
                break

        print(f"Cleared {count} packets from queue.")
    # ---------------------------------------------------------
    # READER THREAD
    # ---------------------------------------------------------

    def start_reader(self):
        print("STARTING READER")
        if self.running:
            print("Reader already running.")
            return

        self.running = True

        self.thread = threading.Thread(
            target=self._reader_loop,
            daemon=True,
        )

        self.thread.start()

        print("Serial reader thread started.")

    def _reader_loop(self):

        print("Reader loop running.")
        
        while self.running:
            print("in_waiting =", self.ser.in_waiting)

            byte = self.ser.read(1)

            if not byte:
                continue

            if byte[0] != DATA_PACKET:
                continue

            payload = self.ser.read(DATA_STRUCT.size)

            if len(payload) != DATA_STRUCT.size:
                print("Incomplete payload")
                continue

            # Decode packet
            time_red_us, tia_red, time_ir_us, tia_ir = \
                DATA_STRUCT.unpack(payload)

            print(
                time_red_us,
                tia_red,
                time_ir_us,
                tia_ir,
            )

            packet = DataPacket(
                time_red_us,
                tia_red,
                time_ir_us,
                tia_ir,
            )

            self.data_packet_que.put(packet)

    def stop_reader(self):

        if not self.running:
            return

        print("Stopping reader thread...")

        self.running = False

        if self.thread is not None:
            self.thread.join(timeout=1)
            self.thread = None

        print("Reader thread stopped.")

    # ---------------------------------------------------------
    # QUEUE
    # ---------------------------------------------------------

    def get_packets(self):

        packets = []

        while True:

            try:
                packet = self.data_packet_que.get_nowait()

            except queue.Empty:
                break

            packets.append(packet)

        return packets

    # ---------------------------------------------------------
    # START / STOP COMMANDS
    # ---------------------------------------------------------

    def start(self):

        self.ser.write(START_CMD)

        time.sleep(0.1)

        if self._wait_for_ack(START_PACKET):

            self.ser.reset_input_buffer()

            print("Arduino acknowledged start.")

            return True

        print("Failed to start.")

        return False

    def stop(self):

        self.ser.write(STOP_CMD)

        time.sleep(0.1)

        if self._wait_for_ack(END_PACKET):

            self.ser.reset_input_buffer()

            print("Arduino end packet acknowledged.")
            print("Recording stopped.")

            return True

        print("Failed to stop.")

        return False

    def _wait_for_ack(self, expected_packet, timeout=2.0):

        deadline = time.time() + timeout

        while time.time() < deadline:

            if self.ser.in_waiting:

                packet = self.ser.read(1)[0]

                if packet == expected_packet:
                    return True

        return False

    # ---------------------------------------------------------
    # CLOSE
    # ---------------------------------------------------------

    def close(self):

        self.stop_reader()

        if self.ser.is_open:
            self.ser.close()

        print("Serial port closed.")
        
# import time
# import serial
# import threading
# import queue
# from communication.packets import (DataPacket,
#                                    START_PACKET, DATA_PACKET, END_PACKET,
#                                    DATA_STRUCT, TOTAL_DATA_SIZE)

# START_CMD = b's'
# STOP_CMD = b'q'

# class SerialManager:
#     ser: serial.Serial

#     def __init__(self, serial_port, baud_rate):
#         self.ser = serial.Serial(serial_port, baud_rate, timeout=0.1)
#         time.sleep(2)
#         self.ser.reset_input_buffer()
        
#         self.data_packet_que = queue.Queue()
#         self.running = False
#         self.thread = None
        
#     def start_reader(self):
#         self.running = True
#         self.thread = threading.Thread(
#             target=self._reader_loop,
#             daemon=True
#         )
#         self.thread.start()

#     def _reader_loop(self):

#         while self.running:

#             if self.ser.in_waiting >= TOTAL_DATA_SIZE:
                
#                 # READ BYTES
#                 header = self.ser.read(1)

#                 if header[0] != DATA_PACKET:
#                     continue

#                 payload = self.ser.read(DATA_STRUCT.size)

#                 if len(payload) != DATA_STRUCT.size:
#                     continue
                
#                 # DECODE PACKET
#                 time_red_us, tia_red, time_ir_us, tia_ir = DATA_STRUCT.unpack(payload)
#                 print(time_red_us, tia_red, time_ir_us, tia_ir)

#                 packet = DataPacket(time_red_us, tia_red, time_ir_us, tia_ir)

#                 # PUT IN QUEUE
#                 self.data_packet_que.put(packet)

#     def get_packets(self):

#         packets = []

#         while True:
#             try:
#                 packets.append(self.data_packet_que.get_nowait())
#             except queue.Empty:
#                 break

#         return packets

#     def close(self):
#         if self.ser.is_open:
#             self.ser.close()
#         print("Serial port closed.")

#     def start(self) -> bool:
#         self.ser.write(START_CMD)
#         time.sleep(0.1)

#         if self._wait_for_ack(START_PACKET):
#             self.ser.reset_input_buffer()
#             print("Arduino acknowledged start.")
#             return True

#         print("Failed to start.")
#         return False

#     def stop(self) -> bool:
        

#         if self._wait_for_ack(END_PACKET):
#             self.ser.reset_input_buffer()
#             print("Arduino end packet acknowledged.")
#             print("Recording stopped.")
#             return True

#         print("Failed to stop.")
#         return False
    
#     def stop_reader(self):

#         self.running = False

#         if self.thread is not None:
#             self.thread.join(timeout=1)
#             self.thread = None


#     def _wait_for_ack(self, expected_packet, timeout=2.0):

#         deadline = time.time() + timeout

#         while time.time() < deadline:

#             if self.ser.in_waiting:
#                 packet = self.ser.read(1)[0]

#                 if packet == expected_packet:
#                     return True

#         return False
