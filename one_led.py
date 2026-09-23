import serial
import matplotlib.pyplot as plt
from collections import deque
import time

# ============================================================
# SETTINGS
# ============================================================

PORT = "COM5"       # Change this to your Arduino COM port
BAUD = 115200

WINDOW_SECONDS = 10
SAMPLE_RATE = 860   # Approximate ADS1115 rate

MAX_POINTS = WINDOW_SECONDS * SAMPLE_RATE


# ============================================================
# SERIAL
# ============================================================

ser = serial.Serial(PORT, BAUD, timeout=0.1)

# Arduino may reset when serial port opens
time.sleep(2)

# Remove anything received during startup
ser.reset_input_buffer()


# ============================================================
# DATA BUFFER
# ============================================================

data = deque(maxlen=MAX_POINTS)
times = deque(maxlen=MAX_POINTS)

start_time = time.time()


# ============================================================
# PLOT
# ============================================================

plt.ion()

fig, ax = plt.subplots()

line, = ax.plot([], [])

ax.set_title("Live PPG - ADS1115")
ax.set_xlabel("Time (s)")
ax.set_ylabel("ADC Counts")

ax.grid(True)


# ============================================================
# MAIN LOOP
# ============================================================

try:

    while True:

        # ----------------------------------------------------
        # Read everything currently available
        # ----------------------------------------------------

        while ser.in_waiting:

            raw = ser.readline().decode(
                "utf-8",
                errors="ignore"
            ).strip()

            try:
                value = int(raw)

                t = time.time() - start_time

                times.append(t)
                data.append(value)

            except ValueError:
                # Ignore malformed serial lines
                pass


        # ----------------------------------------------------
        # Update plot
        # ----------------------------------------------------

        if len(data) > 1:

            line.set_data(times, data)

            # Show most recent WINDOW_SECONDS
            current_time = times[-1]

            ax.set_xlim(
                max(0, current_time - WINDOW_SECONDS),
                current_time
            )

            # Automatically scale Y axis
            minimum = min(data)
            maximum = max(data)

            margin = max(
                (maximum - minimum) * 0.1,
                5
            )

            ax.set_ylim(
                minimum - margin,
                maximum + margin
            )

            fig.canvas.draw()
            fig.canvas.flush_events()


        plt.pause(0.01)


except KeyboardInterrupt:

    print("\nStopping...")


finally:

    ser.close()
    plt.ioff()
    plt.show()