"""SoC OS main"""
import socos.esp32 as pinout
import uasyncio

# from socos.buzzer import Buzzer
from socos.exhaust import Exhaust
from socos.menu import SocMenu
from socos.temperature import Temperature
from socos.watchdog import Watchdog
from socos.window import Window

# Create single task instances

menu = SocMenu(
    pinout.SDA_PIN,
    pinout.SCL_PIN,
    pinout.BUTTON_TOP_LEFT_PIN,
    pinout.BUTTON_TOP_RIGHT_PIN,
    pinout.BUTTON_BOTTOM_LEFT_PIN,
    pinout.BUTTON_BOTTOM_RIGHT_PIN,
)

watchdog = Watchdog(pinout.ONBOARD_LED, 500)
# buzzer = Buzzer(pinout.BUZZER_PWM_PIN, 500)
temperature = Temperature(pinout.TEMPERATURE_PIN)
exhaust = Exhaust(pinout.EXHAUST_HOOD)
window = Window(pinout.WINDOW_REED_PIN, pinout.WINDOW_SABOTAGE_PIN)


# Create SocOS main and start execution
async def main():
    """SoC OS Main Function"""

    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # Init start
    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # temperature.connect_menu(menu)
    # buzzer.connect_menu(menu)
    # temperature.connect_menu(menu)
    # exhaust.connect_menu(menu)
    # watchdog.connect_menu(menu)
    # window.connect_menu(menu)
    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # Init end
    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # BIST start
    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # Start buzzer bist
    # buzzer.bist()
    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # BIST end
    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # TASK start
    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # Start watchdog task
    # watchdog.startThread()
    # Start buzzer task
    # buzzer.startThread()
    # Start temperature measurement task
    temperature.start_thread()
    # Start window control task
    window.start_thread()
    # Start exhaust hood test
    exhaust.on()
    # Start menu task
    # menu.start_thread()

    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # TASK end
    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # MAIN Loop
    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    while True:
        await uasyncio.sleep_ms(1000)
        # Start watchdog task
        watchdog.toggle()
        # Toggle exhaust hood switch
        exhaust.toggle()


uasyncio.run(main())
