import digitalio
import busio
import board
import datetime
import time
import os
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)

# e-ink display modules and setup
from PIL import Image, ImageDraw, ImageFont
from adafruit_epd.epd import Adafruit_EPD
from adafruit_epd.ssd1680 import Adafruit_SSD1680

spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
ecs = digitalio.DigitalInOut(board.CE0)
dc = digitalio.DigitalInOut(board.D22)
rst = digitalio.DigitalInOut(board.D27)
busy = digitalio.DigitalInOut(board.D17)

# color constants
WHITE = (0xFF, 0xFF, 0xFF)
BLACK = (0x00, 0x00, 0x00)
RED = (0xFF, 0x00, 0x00)

# some constants to allow easy resizing of shapes and colors
BORDER = 2
FONTSIZE = 25
BACKGROUND_COLOR = BLACK
FOREGROUND_COLOR = WHITE
TEXT_COLOR = BLACK

font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", FONTSIZE)
tiny_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
medium_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
large_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22)

# setup google spreadsheet
import gspread
from oauth2client.service_account import ServiceAccountCredentials
scope = ["https://spreadsheets.google.com/feeds","https://www.googleapis.com/auth/spreadsheets","https://www.googleapis.com/auth/drive.file","https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("creds2.json", scope)
client = gspread.authorize(creds)
sheet = client.open("Plants").sheet1  # Open the spreadsheet
data = sheet.get_all_records()
last_pressed = sheet.acell('B2').value
print(last_pressed)

# starting text for display and function
prevDate = datetime.datetime.strptime(last_pressed,"%Y-%m-%d %H:%M:%S")
spanDate = datetime.datetime.strptime(last_pressed,"%Y-%m-%d %H:%M:%S")
text = "Plants watered on:"
#text2 = last_pressed
text2 = prevDate.strftime("%m/%d/%Y, %H:%M")
wifi_text = "Wifi up"
wifi_string = "sudo ifconfig wlan0 up"
text3 = "Days Ago"

# toggle wifi on and off
from itertools import cycle
def toggle():
    while True:
        yield ("sudo ifconfig wlan0 down")
        yield ("sudo ifconfig wlan0 up")
  
wifi = toggle()

def render():
    display = Adafruit_SSD1680(     
    122, 250, spi, cs_pin=ecs, dc_pin=dc, sramcs_pin=None, rst_pin=rst, busy_pin=busy,
    )

    display.rotation = 1
    
    image = Image.new("RGB", (display.width, display.height))
    draw = ImageDraw.Draw(image)
    
# Draw a filled box as the background
    draw.rectangle((0, 0, display.width - 1, display.height - 1), fill=BACKGROUND_COLOR)
# Draw a smaller inner foreground rectangle
    draw.rectangle(
        (BORDER, BORDER, display.width - BORDER - 1, display.height - BORDER - 1),
        fill=FOREGROUND_COLOR,
    )

    (font_width, font_height) = font.getsize(text)
    draw1 = draw.text(
             (display.width // 2 - font_width // 2, 22),
        text,
    font=large_font,
    fill=TEXT_COLOR,
    )

    (font_width, font_height) = font.getsize(text)
    draw_wifi = draw.text(
                (((display.width - font_width)+145), 4),
        wifi_text,
    font=small_font,
    fill=TEXT_COLOR,
    )

    (font_width, font_height) = font.getsize(text2)
    draw2 = draw.text(
        (display.width // 2 - font_width // 2, display.height // 2 - font_height // 2),
        text2,
    font=font,
        fill=TEXT_COLOR,
    )

    (font_width, font_height) = font.getsize(text3)
    draw3 = draw.text(
        (display.width // 2 - font_width // 2, 82),
    text3,
    font=font,
    fill=TEXT_COLOR,
    )

# Display image.
    display.image(image)
    display.display()
   

try:
    while True:

            GPIO.setup(6, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            input_state = GPIO.input(6)
            GPIO.setup(5, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            wifi_state = GPIO.input(5)
            now = datetime.datetime.now()
            span = now - spanDate
            elapsed = now - prevDate
            spanDays = round((span.total_seconds()/60/60/24), 10)
            elapsedDays = round((elapsed.total_seconds()/60/60/24), 10)
            print(spanDays, elapsedDays)
            if spanDays >= 1.0:
                spanDate = datetime.datetime.now()
                calc_span = spanDate - prevDate
                print("span days triggered")
                daysAgo = round((calc_span.total_seconds()/60/60/24), 1)
                span_daysAgo = " %s days ago" %(daysAgo)
                text3 = span_daysAgo
                #trigDate =  datetime.datetime.now()
                #text3 = trigDate.strftime("%m/%d/%Y, %H:%M")
                render()
            elif wifi_state == False:
                wifi_string = next(wifi)
                wifi_text = ("Wifi " + wifi_string[19:])
                print(wifi_text)
                #os.system(wifi_string)
                render()
            elif input_state == False:
                time.sleep(0.5)
                #print(wifi_string)
                #if wifi_string == "sudo ifconfig wlan0 down":
                    #wifi_string_up = "sudo ifconfig wlan0 up"
                    #os.system(wifi_string_up)
                    #print("Wifi up")
                    #time.sleep(15)
                now = datetime.datetime.now()
                calc_span = now - prevDate
                print(prevDate)
                daysAgo = round((calc_span.total_seconds()/60/60/24), 1)
                prevDate =  datetime.datetime.now()
                text2 = prevDate
                text2 = prevDate.strftime("%m/%d/%Y, %H:%M")
                text3 = "0 Days Ago"
                wifi_text = "Wifi down"
                render()
                now_format = prevDate.strftime("%Y-%m-%d %H:%M:%S")
                insertRow = ["watered on", now_format, daysAgo]
                #insertRow = ["watered on", prevDate, daysAgo]
                sheet.insert_row(insertRow, 2)
                #wifi_string_down = "sudo ifconfig wlan0 down"
                #os.system(wifi_string_down)
                time.sleep(5)
    
except KeyboardInterrupt:
	print ("Done")