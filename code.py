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
import displayio
import analogio
from adafruit_matrixportal.network import Network
from adafruit_matrixportal.matrix import Matrix
import openweather_graphics 

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

SCROLL_HOLD_TIME = 2  # 2 sec hold of each line before finishing scroll

# --- Weather Unit Setup ---
if UNITS in ("imperial", "metric"):
    gfx = openweather_graphics.OpenWeather_Graphics(
        matrix.display, am_pm=True, units=UNITS
    )
print("gfx loaded")


# --- Sprite Image Parameters ---
SPRITE_FOLDER = "/bmps"
sprite_sheet = "santa.bmp"  #Display image file in folder
current_image = None
current_frame = 0
frame_count = 0
frame_duration = 0.2 #200mS

# --- Sprite Image setup ---
sprite_group = displayio.Group()
sprite_file = SPRITE_FOLDER + "/" + sprite_sheet
bitmap = displayio.OnDiskBitmap(sprite_file)
sprite = displayio.TileGrid(
        bitmap,
        pixel_shader=bitmap.pixel_shader,
        tile_width=bitmap.width,
        tile_height=matrix.display.height,
    )
frame_count = int(bitmap.height / matrix.display.height)
sprite_group.append(sprite)

# --- Timer Parameter Initialization --- 
localtime_refresh = None
weather_refresh = None

#Display and Motion checks
day = None    # 6 = Sun, 0 = Mon
hour = None
min = None
midday = False
active = False
pin = analogio.AnalogIn(board.A0)

while True:
    #Keep screen dark if between hours 10pm and 6am
    if (hour) and (hour < 6 or hour >= 22):
        #Make sure display is shutdown
        matrix.display.root_group = None 
        #check how many minutes left in hour
        min = time.localtime().tm_min
        delay = 60 - min + 1
        time.sleep(delay) #delay to see if next hour
        hour = time.localtime().tm_hour
        day = time. localtime().tm_wday
        continue

    #Keep screen dark if weekend and before 10am
    if day and day > 4:
        if (hour) and (hour < 10):
        #Make sure display is shutdown
        matrix.display.root_group = None 
        #check how many minutes left in hour
        min = time.localtime().tm_min
        delay = 60 - min + 1
        time.sleep(delay) #delay to see if next hour
        hour = time.localtime().tm_hour
        day = time. localtime().tm_wday
        continue
    
    #Chekc if midday 
    if (hour) and (hour > 12 and hour < 5):
        #Make sure display is shutdown
        matrix.display.root_group = None 
        midday = True
        hour = time.localtime().tm_hour
    else:
        midday = False
    
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
    motion = pin.value
    
    #Some time after 6, register trigger to display weather
    if hour < 7 and motion < 1000:
        matrix.display.root_group = None
        continue
    elif hour < 7 and motion > 1000:
        active = True
        current_frame = 0

    #If its after 7am, play the sprites on loop
    if active is False and hour > 7 and midday = False:
        matrix.display.root_group = sprite_group
        current_frame = current_frame + 1
        if current_frame >= frame_count:
            current_frame = 0
        sprite_group[0][0] = current_frame
        time.sleep(frame_duration)

    #If after 7am and motion trigger tripped, select to show weather for set time (in secs) 
    if motion > 1000 and active is False:
        active = True
        current_frame = 0


    #Display weather if selected and before 11pm
    if active is True and hour < 22: 
        gfx.display_weather(value)
        gfx.scroll_next_label()
        # Pause between labels
        time.sleep(SCROLL_HOLD_TIME)    #scroll label
        gfx.scroll_next_label()
        # Pause between labels
        time.sleep(SCROLL_HOLD_TIME)    #scroll label second time
        active = False
        hour = time.localtime().tm_hour    #check hour to see if after 10pm
