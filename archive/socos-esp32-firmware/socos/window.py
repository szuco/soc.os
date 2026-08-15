from time import sleep
from machine import Pin
import uasyncio


class Window:
    """_summary_
    """

    def __init__(self, openPin=0, sabotagePin=4):
        """_summary_

        Args:
            pinNumber (int, optional): _description_. Defaults to 25.
            tick (int, optional): _description_. Defaults to 1000.
        """
        self.reedContactOpen = Pin(openPin, Pin.IN, Pin.PULL_UP)
        self.reedContactSabotage = Pin(sabotagePin, Pin.IN, Pin.PULL_UP)

    async def check_reed_contact_state(self):
        """_summary_
        """
        while True:
            if self.reedContactOpen.value():
                print("open")
            else:
                print("close")
            if self.reedContactSabotage.value():
                print("sabotage")
            else:
                print("no sabotage")
            await uasyncio.sleep(5)

    def start_thread(self):
        """_summary_
        """
        uasyncio.create_task(self.check_reed_contact_state())
