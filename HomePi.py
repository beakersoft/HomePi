#!/usr/bin/python

from time import sleep
from Adafruit_CharLCDPlate import Adafruit_CharLCDPlate
import sys
import subprocess
import re
import time
import datetime
import twitter
import RPi.GPIO as GPIO
import rrdtool
import os
import rrdtool

# Initialize the LCD plate.  Should auto-detect correct I2C bus.  If not,
# pass '0' for early 256 MB Model B boards or '1' for all later versions
lcd = Adafruit_CharLCDPlate()
GPIO.setwarnings(False)

#static stuff
wait_loop = 3
is_dark = False
trend_string = ""
str_pad = " " * 16
date_twitter_cache = datetime.datetime.now()
twitter_loc_code = 23424975
twitter_cons_key = "WvaGiKWM7vwz0mqulZv2w" 
twitter_cons_sec = "fBO3JTrwwZ9dwJRrca6jFcFrhDzox6oXMhWajvaY" 
twitter_access_key = "101849409-Di2Uh1Trdv9Cqg5RZCJkVONtxSIoMJihnvHjq0CR" 
twitter_access_sec = "NikB3wNxQ92lWxHovixjcweQ3sj46qJZmAob9JeiHA"

log_rrd = True
rrd_root = "/home/pi/HomePi/RRDFiles/" 
temp_app_root = "/home/pi/HomePi/"
rrd_graph_root = "/var/www/homepi/graphs/" 

#Functions
####################################################################

#Function to get the reading from the light sensor on the passed pin
def RCtime (RCpin):
	GPIO.setmode(GPIO.BCM)
	reading = 0
	GPIO.setup(RCpin, GPIO.OUT)
	GPIO.output(RCpin, GPIO.LOW)
	time.sleep(0.1)

	GPIO.setup(RCpin, GPIO.IN)
	while (GPIO.input(RCpin) == GPIO.LOW):
		reading +=1
	GPIO.cleanup()
	return reading

#Function to log data to an rrd file
def LogToRRD (rrdKey, rrdValue, rrdDevice, graphLabel, graphColour):

	#first see if we need to create a file for this device	
	if not os.path.exists(rrd_root + rrdDevice + ".rrd"):
		print "need the file\n"
		ret = rrdtool.create(rrd_root + rrdDevice + ".rrd", "--step", "60",
 		"DS:" + rrdKey + ":GAUGE:120:-273:5000",
 		"RRA:AVERAGE:0.5:1:1200",
 		"RRA:MIN:0.5:12:2400",
 		"RRA:MAX:0.5:12:2400",
 		"RRA:AVERAGE:0.5:12:2400")	

	#now we should have the file, so lets try to update it
	ret = rrdtool.update(rrd_root + rrdDevice + ".rrd", 'N:' + str(rrdValue));

	#now graph the action, hourly, daily, monthly, yearly
	ret = rrdtool.graph(rrd_graph_root + rrdDevice + "_hour.png", "--start", "-4h", "--title=" + rrdDevice.title() + " Last Hour", 
	"DEF:" + rrdKey + "=" + rrd_root + rrdDevice + ".rrd:" + rrdKey + ":AVERAGE",
	"LINE1:" + rrdKey + graphColour + ":" + rrdKey + " " + graphLabel)	

	ret = rrdtool.graph(rrd_graph_root + rrdDevice + "_daily.png", "--start", "-4d", "--title=" + rrdDevice.title() + " Current Day",
        "DEF:" + rrdKey + "=" + rrd_root + rrdDevice + ".rrd:" + rrdKey + ":AVERAGE",
        "LINE1:" + rrdKey + graphColour + ":" + rrdKey + " " + graphLabel)	

	ret = rrdtool.graph(rrd_graph_root + rrdDevice + "_monthly.png", "--start", "-1m", "--title=" + rrdDevice.title() + " Current Month",
        "DEF:" + rrdKey + "=" + rrd_root + rrdDevice + ".rrd:" + rrdKey + ":AVERAGE",
        "LINE1:" + rrdKey + graphColour + ":" + rrdKey + " " +  graphLabel)

	ret = rrdtool.graph(rrd_graph_root + rrdDevice + "_yearly.png", "--start", "-1y", "--title=" + rrdDevice.title() + " Current Year",
        "DEF:" + rrdKey + "=" + rrd_root + rrdDevice + ".rrd:" + rrdKey + ":AVERAGE",
        "LINE1:" + rrdKey + graphColour + ":" + rrdKey + " " +  graphLabel) 

####################################################################

#create the twitter API object
api = twitter.Api(consumer_key=twitter_cons_key,
                      consumer_secret=twitter_cons_sec,
                      access_token_key=twitter_access_key,
                      access_token_secret=twitter_access_sec)

while(True):

	light_lev = RCtime(23)	
	if light_lev > 10:
		is_dark = True
	else:
		is_dark = False	

	#here we go and get the current temp/humidity and log if needed. Display on screen if its daylight later
	output = subprocess.check_output([temp_app_root + "/Adafruit_DHT", "11", "17"]);
        matches = re.search("Temp =\s+([0-9.]+)", output)
        if (not matches):
	        time.sleep(3)
                continue                #continue should work in our loop, and stop us dropping out into an error
        temp = float(matches.group(1))

        #search for humidity printout
        matches = re.search("Hum =\s+([0-9.]+)", output)
        if (not matches):
        	time.sleep(3)
                continue
        humidity = float(matches.group(1))

	#now if we want to log the info to rrd, do that here
        if log_rrd == True:
        	LogToRRD("Temperature",temp,"temp", "[deg C]", "#CC0000")
                LogToRRD("Humidity",humidity,"humid", "[%]", "#0D4F8B")		

	#its not dark, so we are going to use the lcd screen to show our info
	if not is_dark:

		#turn of the 'street light' first
		GPIO.setmode(GPIO.BOARD)  
		GPIO.setup(12, GPIO.OUT)
		GPIO.output(12,GPIO.LOW)	

		#Clear the lcd and set the colour
		lcd.clear()
		lcd.backlight(lcd.ON)

		#first output the date and time
		localtime = time.asctime( time.localtime(time.time()))
		lcd.clear()	
		lcd.message(localtime)
		sleep(wait_loop)

		#Now we should have them, put them to the lcd
		lcd.clear()
		lcd.message("Temp:     %.1f C" % temp + "\nHumidity: %.1f %%" % humidity)

		now = datetime.datetime.now()
		#print str(datetime.datetime.now() + "Temp: %.1f C" % temp
		sleep(wait_loop)

		#if the trend string is empty or we are passed the last 5 min check, update the trend list	
		twr_date = datetime.datetime.now() - date_twitter_cache		

		if (twr_date.seconds > 300)or (trend_string == ""): 
			try: 
				trend_string = ""
				for trend in api.GetTrendsWoeid(twitter_loc_code):
       		 			trend_string += " " + trend.name
				trend_string = str_pad + trend_string
				date_twitter_cache = datetime.datetime.now()	
			except:
				trend_string = "Could not get the twitter trends!!!"

		#now we are going to try and 'scroll' the string across the lcd
		for i in range (0, len(trend_string)):
			lcd_text = trend_string[i:(i+15)]
			lcd.clear()
			lcd.message("Trending\n" + lcd_text)
			sleep(0.4)

		#now we are going to see if the light is on or not
		lcd.clear()
		lcd.message("Light Level " + str(RCtime(23)))	
		sleep(wait_loop)
	else:
		#its dark, so turn the light on, LCD off and wait a mo until we check again
		lcd.clear()
		lcd.backlight(lcd.OFF)

		#turn on the street light!
		GPIO.setmode(GPIO.BOARD)
		GPIO.setup(12, GPIO.OUT) 
		GPIO.output(12,GPIO.HIGH)
		sleep(10)	

lcd.clear()
lcd.backlight(lcd.OFF)
sys.exit()
