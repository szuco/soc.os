"""Module providing functions for menu handling."""
from time import sleep, sleep_ms

import uasyncio
from drivers.ssd1306 import SSD1306_I2C as DISPLAY
from gui.umenu import *
from machine import Pin, SoftI2C

# class Config:

#     def __init__(self, name):
#         #super().__init__(name)
#         self.statuses = {}

#     def get_status(self, *args):
#         try:
#             return self.statuses[args[0]]
#         except KeyError:
#             self.statuses[args[0]] = False
#             return False

#     def toggle(self, *args):
#         self.statuses[args[0]] = not self.statuses[args[0]]
#         self.get_status(*args)
# """


class DrawCustomScreen(CustomItem):
    def __init__(self, name):
        super().__init__(name)

    def select(self):
        return (
            self.parent
        )  # this is needed to go back to previous view when SET button is pushed

    def draw(self):
        if self.display:
            self.display.fill(0)
            self.display.rect(0, 0, self.display.width, self.display.height, 1)
            self.display.text("SHOW SOME TEXT", 0, 10, 1)
            self.display.hline(0, 32, self.display.width, 1)
            self.display.show()


class SocMenu:
    """_summary_"""

    def __init__(
        self,
        dispSDA=21,
        dispSCL=22,
        pinTopLeft=33,
        pnTopRight=25,
        pinBottomLeft=32,
        pinBottomRight=26,
    ):
        """_summary_

        Args:
            pinNumber (int, optional): _description_. Defaults to 25.
            tick (int, optional): _description_. Defaults to 1000.
        """
        self.buttonTopLeft = Pin(pinTopLeft, Pin.IN, Pin.PULL_UP)
        self.buttonTopRight = Pin(pnTopRight, Pin.IN, Pin.PULL_UP)
        self.buttonBottomLeft = Pin(pinBottomLeft, Pin.IN, Pin.PULL_UP)
        self.buttonBottomRight = Pin(pinBottomRight, Pin.IN, Pin.PULL_UP)
        # using SoftI2C
        i2c = SoftI2C(sda=Pin(dispSDA), scl=Pin(dispSCL))
        print(i2c.scan())

        # wifi = WifiActions('WiFi Info')
        # config = Config('Config')

        # using uMenu
        self.display = DISPLAY(128, 64, i2c)
        self.menu = Menu(self.display, 4, 8)
        self.menu.set_screen(
            MenuScreen("Einstellungen")
            .add(SubMenuItem("WiFi"))
            # .add(wifi)
            # .add(ToggleItem('Activate', wifi.get_status, wifi.activate)))
            .add(
                SubMenuItem("Lights")
                # .add(ToggleItem('Headlight', (config.get_status, 1), (config.toggle, 1)))
                # .add(ToggleItem('Backlight', (config.get_status, 2), (config.toggle, 2)))
                .add(SubMenuItem("LEDs"))
            )
            # .add(ToggleItem('Turn ON', (config.get_status, 3), (config.toggle, 3)))))
            .add(
                SubMenuItem("Main Info")
                .add(InfoItem("Status:", "ok"))
                .add(InfoItem("Temp:", "45.1"))
            )
            .add(DrawCustomScreen("Text in frame"))
        )
        self.menu.main_screen

        self.menu.draw()

        self.buttonTopLeft.irq(self.menu_ok, Pin.IRQ_FALLING)
        self.buttonTopRight.irq(self.menu_up, Pin.IRQ_FALLING)
        self.buttonBottomRight.irq(self.menu_down, Pin.IRQ_FALLING)
        self.buttonBottomLeft.irq(self.menu_home, Pin.IRQ_FALLING)

    def menu_ok(self, pin):
        """_summary_

        Args:
            pin (_type_): _description_
        """
        sleep_ms(50)
        if pin.value() == 0:
            print("select")
            self.menu.click()

    def menu_up(self, pin):
        """_summary_

        Args:
            pin (_type_): _description_
        """
        sleep_ms(50)
        if pin.value() == 0:
            print("move up")
            self.menu.move(-1)

    def menu_down(self, pin):
        """_summary_

        Args:
            pin (_type_): _description_
        """
        sleep_ms(50)
        if pin.value() == 0:
            print("move down")
            self.menu.move(1)

    def menu_home(self, pin):
        """_summary_

        Args:
            pin (_type_): _description_
        """
        sleep_ms(50)
        if pin.value() == 0:
            print("move home")
            self.menu.reset()

    async def check_button_state(self):
        """_summary_"""
        while True:
            await uasyncio.sleep_ms(100)
            self.display.fill(0)
            if self.buttonTopLeft.value():
                self.display.text("RELEASED", 0, 0)
            else:
                self.display.text("PRESSED", 0, 0)
            if self.buttonTopRight.value():
                self.display.text("RELEASED", 0, 10)
            else:
                self.display.text("PRESSED", 0, 10)
            if self.buttonBottomLeft.value():
                self.display.text("RELEASED", 0, 20)
            else:
                self.display.text("PRESSED", 0, 20)
            if self.buttonBottomRight.value():
                self.display.text("RELEASED", 0, 30)
            else:
                self.display.text("PRESSED", 0, 30)
            self.display.show()

    def start_thread(self):
        """_summary_"""
        uasyncio.create_task(self.check_button_state())
