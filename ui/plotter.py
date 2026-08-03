import matplotlib.animation as animation
import matplotlib.pyplot as plt
import matplotlib


class Plotter:

    def __init__(self, mode, title, output_dir, time_window, processor, serial_manager, recorder, live_data, estimator):

        self.mode = mode
        self.title = title
        self.output_dir = output_dir
        self.time_window = time_window
        self.processor = processor
        self.data_source = serial_manager
        self.recorder = recorder
        self.live_data = live_data
        self.estimator = estimator
        
        if self.data_source.start():
            self.data_source.start_reader()   # <-- ADD THIS
            self.is_running = True
            print("Recording started.")

        self.is_running = False

        self.y_min = -10
        self.y_max = 10

        self.animation = None
        self._create_figure()

    def _create_figure(self):
        self.fig, (self.ax_red, self.ax_ir, self.ax_spo2) = plt.subplots(3, 1, sharex=True)

        self.red_line, = self.ax_red.plot([], [], color="red", label="Red")
        self.ir_line, = self.ax_ir.plot([], [], color="black", label="IR")
        self.spo2_line, = self.ax_spo2.plot([], [], color="blue", label="SpO2")

        self.ax_red.set_ylim(self.y_min, self.y_max)
        self.ax_red.set_xlabel("Time (s)")
        self.ax_red.set_ylabel("ADC")
        self.ax_red.grid(True)
        self.ax_red.legend()
        self.ax_red.set_title(self.title)

        self.ax_ir.set_ylim(self.y_min, self.y_max)
        self.ax_ir.set_xlabel("Time (s)")
        self.ax_ir.set_ylabel("ADC")
        self.ax_ir.grid(True)
        self.ax_ir.legend()

        self.ax_spo2.set_ylim(90, 100)
        self.ax_spo2.set_xlabel("Time (s)")
        self.ax_spo2.set_ylabel("SpO2 (%)")
        self.ax_spo2.grid(True)
        self.ax_spo2.legend()

        self.fig.canvas.mpl_connect(
            "key_press_event",
            self.on_key_press,
        )

    def run(self):
        # redraw every 0.2 s
        self.animation = animation.FuncAnimation(
            self.fig,
            self.update_plot,
            interval=200, 
            cache_frame_data=False,
        )

        print(matplotlib.get_backend())

        plt.show()

    def update_plot(self, frame):

        if not self.is_running:
            return

        # LIVE MODE
        packets = self.data_source.get_packets()

        for packet in packets:
            self.process_packet(packet)

        self.redraw()

        return self.red_line, self.ir_line, self.spo2_line

    def process_packet(self, packet):
        # print('process packet')
        self.recorder.append(packet)
        print(packet.time_red_us)
        filtered_packet = self.processor.update(packet)

        if filtered_packet is None:
            return

        self.recorder.append(filtered_packet)
        self.live_data.append(filtered_packet)
        
        result = self.estimator.update(filtered_packet)

        if result is not None:

            curr_spo2_packet, display_spo2_packet = result

            if curr_spo2_packet is not None:
                self.recorder.append(curr_spo2_packet)

            if display_spo2_packet is not None:
                self.live_data.append(display_spo2_packet)

    def redraw(self):
        # print('redraw')
        self.red_line.set_data(
            self.live_data.t_red,
            self.live_data.red_full,
        )

        self.ir_line.set_data(
            self.live_data.t_ir,
            self.live_data.ir_full,
        )

        self.spo2_line.set_data(
            self.live_data.spo2_t,
            self.live_data.spo2_v,
        )

        self.update_axes()

        self.autoscale(self.ax_red, self.live_data.red_full)
        self.autoscale(self.ax_ir, self.live_data.ir_full)
        self.autoscale(self.ax_spo2, self.live_data.spo2_v)

        self.fig.canvas.draw_idle()

    def update_axes(self):

        latest = 0.0

        if self.live_data.t_red:
            latest = self.live_data.t_red[-1]

        if self.live_data.t_ir:
            latest = max(latest, self.live_data.t_ir[-1])

        if not self.live_data.t_red and not self.live_data.t_ir:
            return

        left = max(0.0, latest - self.time_window)
        right = left + self.time_window

        for ax in (self.ax_red, self.ax_ir, self.ax_spo2):
            ax.set_xlim(left, right)

    def on_key_press(self, event):

        if event.key == "enter":

            if not self.is_running:
                self.start()

        elif event.key == "z":

            if self.is_running:
                self.stop()

    def start(self):

        self.live_data.clear()
        self.recorder.clear()
        self.processor.reset()
        self.estimator.reset()

        # Make absolutely sure old reader isn't running
        self.data_source.stop_reader()

        # Remove stale packets
        self.data_source.clear_queue()

        # Start Arduino
        if self.data_source.start():

            # Now receive only new packets
            self.data_source.start_reader()

            self.is_running = True

            print("Recording started.")
            
    def stop(self):

        print("Stopping...")

        self.data_source.stop_reader()

        if self.data_source.stop():

            print("serial stopped")

            self.is_running = False

            print("is_running =", self.is_running)

            plot_name = f'{self.output_dir}/{self.title}.png'

            self.fig.savefig(
                plot_name,
                dpi=300,
            )

            print(f"Saved plot to {plot_name}")

            print("Recording stopped.")

    @staticmethod
    def autoscale(ax, y):

        if len(y) < 2:
            return

        ymin = min(y)
        ymax = max(y)

        if ymin == ymax:
            margin = 1
        else:
            margin = 0.05 * (ymax - ymin)

        ax.set_ylim(
            ymin - margin,
            ymax + margin,
        )
