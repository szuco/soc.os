import time
from machine import Pin

class Watchdog:

    pin = Pin(25, Pin.OUT)

    def __init__(self):        
        pass

    def toggle(self, tick):
        self.pin.toggle()
        time.sleep_ms(tick)
