"""Module providing functions for buzzer handling."""
import ds18x20
import machine
import onewire
import uasyncio
from gui.umenu import *


class MainScreen(CustomItem):
    def __init__(self, name):
        super().__init__(name)
        self.status = False

    def select(self):
        return self.parent

    def draw(self):
        # self.display.fill(0)
        # self.display.rect(0, 0, self.display.width, self.display.height, 1)
        self._centered_text("ID: " + self.get_id(), 20, 1)
        self._centered_text("Temp: " + self.get_temp(), 34, 1)
        # self.display.show()

    def get_id(self):
        """Return default device id

        Returns:
            string: device id
        """
        return "00_00_00_00_00_00_00_00"

    def get_temp(self):
        """Return default temperature value

        Returns:
            string: temperature
        """
        return "21.05°C"

    def get_status(self):
        """Return menu visible or hidden state

        Returns:
            bool: True for visible and False for hidden
        """
        return self.status

    def activate(self):
        """Set menu state to visible"""
        self.status = not self.status
        self.get_status()

    def _centered_text(self, text, y, c):
        pass
        # x = int(self.display.width / 2 - len(text) * 8 / 2)
        # self.display.text(text, x, y, c)


class Temperature(MainScreen):
    """Class for temperature back end and front end handling based on an DS18X20 chip"""

    def __init__(self, pin_number=14):
        super().__init__(self)
        self.pin_number = pin_number
        self.pin = None
        self.roms = None
        self.sensor = None

    def connect(self):
        """Reinitialize the DS18X20 chip"""
        self.pin = machine.Pin(self.pin_number)
        if self.pin:
            self.sensor = ds18x20.DS18X20(onewire.OneWire(self.pin))
            self.roms = None
            if self.sensor:
                self.roms = self.sensor.scan()

    def is_connected(self):
        """_summary_"""
        self.roms = None
        if self.sensor:
            self.roms = self.sensor.scan()
        return self.roms is not None

    def print_scan_result(self):
        """Print number of devices found and there ids"""
        if self.roms:
            print("Found ", len(self.roms), " DS devices: ", self.roms)
        else:
            print("No devices found or loaded.")

    def get_current_temperature(self, sensor_num):
        """Return temperature of the specified sensor

        Args:
            sensorNum (integer): Number of sensor a list of found sensors

        Returns:
            float: Temperature value with 2 decimal places
        """
        return (
            self.sensor.read_temp(self.roms[sensor_num])
            if self.sensor and self.roms and sensor_num <= len(self.roms)
            else -1.0
        )

    def add_underscore(self, myString, group=2, char="_"):
        """_summary_

        Args:
            myString (_type_): _description_
            group (int, optional): _description_. Defaults to 2.
            char (str, optional): _description_. Defaults to "_".

        Returns:
            _type_: _description_
        """
        myString = str(myString)
        return char.join(
            myString[i : i + group] for i in range(0, len(myString), group)
        )

    def get_device_id(self, sensor_num):
        """_summary_

        Args:
            sensor_num (_type_): _description_

        Returns:
            _type_: _description_
        """
        return self.add_underscore(
            hex(int.from_bytes(bytes(self.roms[sensor_num])[2:], "big"))
            if self.sensor and self.roms and sensor_num <= len(self.roms)
            else -1.0
        ).upper()

    def get_id(self):
        return self.get_device_id(1)

    def get_temp(self):
        return self.get_current_temperature(1)

    async def acquire_temperatures(self):
        """Main task loop of temperature measurement"""
        while True:
            await uasyncio.sleep_ms(750)
            if not self.is_connected():
                print("Try to connect")
                self.connect()
                self.print_scan_result()
            else:
                try:
                    self.sensor.convert_temp()
                    for rom in self.roms:
                        id = self.add_underscore(
                            hex(int.from_bytes(bytes(rom), "big"))[2:]
                        ).upper()
                        if self.activate():
                            self.draw()
                        print(self.sensor.read_temp(rom))
                except Exception:
                    print("Device lost")
            await uasyncio.sleep(5)

    def start_thread(self):
        """Start task execution thread"""
        uasyncio.create_task(self.acquire_temperatures())
