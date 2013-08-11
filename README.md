 HomePi Readme
==============

HomePi is a project based around a Rapberry Pi. The point of the project was to build the Pi into a Lego house with an LCD screen as the output device, and use the Pi and a custom pcb to display and monitor various bits of info. You can download the files to create your own pcb from XXXX, create your own version or just plug all the components into a breadboard

Installation
------------

There are a couple of things you need to install first before the script in its current state will work.

- Python -  Should already be installed on your Pi is your are using one of the popular Distros. Script is written in Python
- Git - Used to pull down the various projects onto your Pi
- Apache2 - Used to view the graphs being created 
- RRDTool - Used to create graphs from the temperature and humidity
- Extra python extensions for twitter and rrd
- If you are using the Adafruit LCD screen check out [this artical as well](http://learn.adafruit.com/drive-a-16x2-lcd-directly-with-a-raspberry-pi/overview)
- If you are going to use any 1-Wire devices this needs enabling in the kernal

So running the following should get you into a ready to run state

```
sudo apt-get install git-core
sudo apt-get install apache2
mkdir /var/www/homepi/graphs/
sudo apt-get rrdtool
sudo apt-get install python-rrd
```
For the twitter python librarys see [here](https://github.com/bear/python-twitter)

Then, drop into wherever you want to run the script from, and run 

```
git clone https://github.com/beakersoft/HomePi.git
```

Now all thats left to do is edit the HomePi.py script with your own details for the twitter api. At the top of the script, fill in your details for

```python
twitter_loc_code 
twitter_cons_key 
twitter_cons_sec
twitter_access_key
twitter_access_sec
```
Run the script by running ./HomePi.py as root. You also might want to add it to init.d so it you can run it as a startup script
