# SPDX-FileCopyrightText: 2020 John Park for Adafruit Industries
#
# SPDX-License-Identifier: MIT

# Matrix Weather display
# For Metro M4 Airlift with RGB Matrix shield, 64 x 32 RGB LED Matrix display

"""
This example queries the Open Weather Maps site API to find out the current
weather for your location... and display it on a screen!
if you can find something that spits out JSON data, we can display it
"""
import time
import board
import microcontroller
import displayio
from digitalio import DigitalInOut, Direction, Pull
from adafruit_matrixportal.network import Network
from adafruit_matrixportal.matrix import Matrix
import openweather_graphics  # pylint: disable=wrong-import-position
import sprite_graphics #scrolls through sprite animation

# Get wifi details and more from a secrets.py file
try:
    from secrets import secrets
except ImportError:
    print("WiFi secrets are kept in secrets.py, please add them there!")
    raise

# --- Display Setup ---
matrix = Matrix(rotation=180)
network = Network(status_neopixel=board.NEOPIXEL, debug=True)

# --- Weather Unit Selection ---
if hasattr(board, "D12"):
    jumper = DigitalInOut(board.D12)
    jumper.direction = Direction.INPUT
    jumper.pull = Pull.UP
    is_metric = jumper.value
elif hasattr(board, "BUTTON_DOWN") and hasattr(board, "BUTTON_UP"):
    button_down = DigitalInOut(board.BUTTON_DOWN)
    button_down.switch_to_input(pull=Pull.UP)

    button_up = DigitalInOut(board.BUTTON_UP)
    button_up.switch_to_input(pull=Pull.UP)
    if not button_down.value:
        print("Down Button Pressed")
        microcontroller.nvm[0] = 1
    elif not button_up.value:
        print("Up Button Pressed")
        microcontroller.nvm[0] = 0
    print(microcontroller.nvm[0])
    is_metric = microcontroller.nvm[0]
else:
    is_metric = False

if is_metric:
    UNITS = "metric"  # can pick 'imperial' or 'metric' as part of URL query
    print("Jumper set to metric")
else:
    UNITS = "imperial"
    print("Jumper set to imperial")

# --- Weather Location Setup ---
# Use cityname, country code where countrycode is ISO3166 format.
# E.g. "New York, US" or "London, GB"
LOCATION = "Los Angeles, US"
print("Getting weather for {}".format(LOCATION))
# Set up from where we'll be fetching data
DATA_SOURCE = (
    "http://api.openweathermap.org/data/2.5/weather?q=" + LOCATION + "&units=" + UNITS
)
DATA_SOURCE += "&appid=" + secrets["openweather_token"]
# You'll need to get a token from openweather.org, looks like 'b6907d289e10d714a6e88b30761fae22'
# it goes in your secrets.py file on a line such as:
# 'openweather_token' : 'your_big_humongous_gigantor_token',
DATA_LOCATION = []
SCROLL_HOLD_TIME = 0  # set this to hold each line before finishing scroll

# --- Weather Unit Setup ---
if UNITS in ("imperial", "metric"):
    gfx = openweather_graphics.OpenWeather_Graphics(
        matrix.display, am_pm=True, units=UNITS
    )
print("gfx loaded")

# ---Sprite Load --- 
sprt = sprite_graphics.sprite_graphics(matrix.display)

# --- Sprite Image setup ---
current_image = None
current_frame = 0
frame_count = 0
frame_duration = 0.1 #100mS

# --- Parameter Initialization --- 
localtime_refresh = None
weather_refresh = None
weather_loop = None

#Display and Motion checks
hour = None
min = None
active = False

while True:
    #Keep screen dark if between hours 10pm and 6am
    if hour <= 6 or hour >= 22:
        #Make sure things are shutdown
        matrix.display.root_group = None 
        #check how many minutes left in hour
        min = time.localtime().tm_min
        delay = 60 - min
        time.sleep(delay) #delay to see if next hour
        hour = time.localtime().tm_hour
        continue
    
    # only query the online time once per hour (and on first run)
    if (not localtime_refresh) or (time.monotonic() - localtime_refresh) > 3600:
        try:
            print("Getting time from internet!")
            network.get_local_time()
            localtime_refresh = time.monotonic()
            hour = time.localtime().tm_hour
        except RuntimeError as e:
            print("Some error occured, retrying! -", e)
            continue
    
    # only query the weather every 10 minutes (and on first run)
    if (not weather_refresh) or (time.monotonic() - weather_refresh) > 600:
        try:
            value = network.fetch_data(DATA_SOURCE, json_path=(DATA_LOCATION,))
            print("Response is", value)
            weather_refresh = time.monotonic()
        except RuntimeError as e:
            print("Some error occured, retrying! -", e)
            continue
    
    #Measure the motion sensor, baseline ~300, above 3000 means tripped  
    motion = AnalogRead(board.A0)
    
    #Some time after 6
    if hour < 7 and motion < 1000:
        continue
    
    if motion > 1000 and active is False:
        active = True
        weather_loop = time.monotonic()
        current_frame = 0
    elif time.monotonic - weather_loop > 60:
        active = False
        
    ### FIGURE OUT HOW TO SWITCH BETWEEN DISPLAY TYPES AFTER TRIGGER
    if active is True and hour <22:
        gfx.display_weather(value)
        gfx.scroll_next_label()
        # Pause between labels
        time.sleep(SCROLL_HOLD_TIME)
    elif active is False and hour <22:
        sprt.display(current_frame)
        current_frame = current_frame + 1
    else:
        #Keep screen off
        matrix.display.root_group = None
