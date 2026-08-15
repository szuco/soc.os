import uasyncio
import time
from machine import Pin


class Watchdog:
    """_summary_
    """

    def __init__(self, pinNumber=25, tick=1000):
        """_summary_

        Args:
            pinNumber (int, optional): _description_. Defaults to 25.
            tick (int, optional): _description_. Defaults to 1000.
        """
        self.pin = Pin(pinNumber, Pin.OUT)
        self.tick = tick

    def toggle(self):
        """_summary_
        """
        self.pin.value(not self.pin.value())

    async def toggleThread(self):
        while True:
            self.toggle()
            await uasyncio.sleep_ms(self.tick)

    def startThread(self):
        uasyncio.create_task(self.toggleThread())
