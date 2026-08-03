import time
import threading
import queue
import pandas as pd

from communication.packets import DataPacket


class ReplayManager:
    """
    Replays a previously recorded CSV as if it were coming from
    the Arduino.

    Interface matches SerialManager:

        start()
        start_reader()
        get_packets()
        stop_reader()
        clear_queue()
        stop()
        close()

    realtime=False:
        Replay packets as fast as possible.

    realtime=True:
        Replay packets according to the timestamps in the CSV.
    """

    def __init__(self, csv_path, realtime=False):

        self.csv_path = csv_path
        self.realtime = realtime

        self.df = pd.read_csv(self.csv_path)
        self.rows = list(self.df.itertuples(index=False))

        self.index = 0

        self.data_packet_que = queue.Queue()

        self.running = False
        self.thread = None

    # =========================================================
    # READER THREAD
    # =========================================================

    def start_reader(self):

        if self.running:
            print("Replay reader already running.")
            return

        self.running = True

        self.thread = threading.Thread(
            target=self._reader_loop,
            daemon=True,
        )

        self.thread.start()

        print("Replay reader thread started.")

    def _reader_loop(self):

        print("Replay reader loop running.")

        while self.running:

            if self.index >= len(self.rows):
                self.running = False
                break

            row = self.rows[self.index]

            # -------------------------------------------------
            # REAL-TIME DELAY
            # -------------------------------------------------

            if self.realtime and self.index > 0:

                prev = self.rows[self.index - 1]

                dt = (
                    int(row.Time_red_us)
                    - int(prev.Time_red_us)
                ) / 1e6

                if dt > 0:

                    # Sleep in small increments so stop_reader()
                    # doesn't have to wait for a long sleep.
                    end_time = time.monotonic() + dt

                    while self.running:

                        remaining = end_time - time.monotonic()

                        if remaining <= 0:
                            break

                        time.sleep(min(remaining, 0.01))

            if not self.running:
                break

            # -------------------------------------------------
            # CREATE PACKET
            # -------------------------------------------------

            packet = DataPacket(
                time_red_us=int(row.Time_red_us),
                red=int(row.tia_red),
                time_ir_us=int(row.Time_ir_us),
                ir=int(row.tia_ir),
            )

            # -------------------------------------------------
            # PUT PACKET INTO QUEUE
            # -------------------------------------------------

            self.data_packet_que.put(packet)

            self.index += 1

        print("Replay reader loop stopped.")

    # =========================================================
    # QUEUE
    # =========================================================

    def get_packets(self):

        packets = []

        while True:

            try:
                packet = self.data_packet_que.get_nowait()

            except queue.Empty:
                break

            packets.append(packet)

        return packets

    def clear_queue(self):

        count = 0

        while True:

            try:
                self.data_packet_que.get_nowait()
                count += 1

            except queue.Empty:
                break

        print(f"Cleared {count} replay packets.")

    # =========================================================
    # START / STOP
    # =========================================================

    def start(self):

        print("Replay started.")

        self.index = 0
        self.running = False

        self.clear_queue()

        return True

    def stop_reader(self):

        if not self.running:
            return

        print("Stopping replay reader...")

        self.running = False

        if self.thread is not None:

            self.thread.join(timeout=1)

            self.thread = None

        print("Replay reader stopped.")

    def stop(self):

        print("ReplayManager.stop()")

        self.stop_reader()

        return True

    # =========================================================
    # CLOSE
    # =========================================================

    def close(self):

        self.stop_reader()
        self.clear_queue()

        print("ReplayManager closed.")