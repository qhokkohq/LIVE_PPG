
class KeyboardController:

    def __init__(self, plotter):
        self.plotter = plotter

    def connect(self):
        self.plotter.fig.canvas.mpl_connect(
            "key_press_event",
            self.on_key_press,
        )

    def on_key_press(self, event):

        match event.key:

            case "enter":
                self.plotter.start()

            case "z":
                self.plotter.stop()

