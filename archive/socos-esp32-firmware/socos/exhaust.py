import time
from machine import Pin


class Exhaust:
    """_summary_
    """

    def __init__(self, pinNumber=12):
        """_summary_

        Args:
            pinNumber (int, optional): _description_. Defaults to 25.
            tick (int, optional): _description_. Defaults to 1000.
        """
        self.pin = Pin(pinNumber, Pin.OUT)

    def toggle(self):
        """_summary_
        """
        self.pin.value(not self.pin.value())

    def on(self):
        self.pin.value(True)

    def off(self):
        self.pin.value(False)
