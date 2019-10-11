# Hue Thief


Factory reset Philips Hue bulbs using an EZSP-based Zigbee USB stick. After a reset, bulbs can easily join any type of compatible bridge.


## EZSP-based Zigbee USB sticks

These are devices based on a Silicon Labs EM351, EM357 or EM358 chip that communicates with the host PC using the EZSP protocol over a virtual COM port. Which protocol is used depends on which firmware is flashed.

- Silicon Labs/Linear/Nortek/GoControl HubZ/QuickStick Combo (HUSBZB-1)/Elelabs Raspberry Pi shield and USB adapter. These devices should come with an EZSP firmware preloaded.
- Silicon Labs/Telegesis ETRX357USB/ETRX3USB/ETRX3. These devices come with an AT-command based firmware preloaded. You may be able to flash it with compatible firmware by doing something like this: https://community.home-assistant.io/t/eu-usb-sticks-for-the-new-zigbee-component/16718/10?u=frank



## Installation

Make sure you have python v3 and pip. (`sudo apt-get install python3-pip`)

```sh
git clone https://github.com/vanviegen/hue-thief
cd hue-thief
pip3 install --user -r requirements.txt
```


## Usage

Bring the bulb(s) you want to factory reset close to your EZSP device. Shutdown any other applications (home assistant, perhaps?) that may be using the EZSP device. Power on the bulb(s) and immediately:

```sh
python3 hue-thief /dev/ttyUSB0
```

`/dev/ttyUSB0` should be your EZSP device. You should have full permissions on this device file.

In case you're using Ubuntu on Windows (WSL) you'll want to do something like this, assuming the EZSP device is mapped to COM4:

```sh
sudo python3 ./hue-thief.py /dev/ttyS4
```

Hue Thief will now scan all Zigbee channels for ZLL-compatible bulbs that are associated with any Zigbee network. When a bulb is found, it will blink a couple of times, and the application will ask if you want to factory reset this bulb. (If you didn't see any blinking, you may be doing your neighbours a favour by choosing 'N' here. :-))

That's it. Your now factory clean bulbs should be discoverable through whatever means your bridge/software offers.


## Docker image

If you already have Docker set up, then it is very simple to build a new image for Hue Thief.


### Dockerfile
```
FROM python:3
RUN git clone https://github.com/vanviegen/hue-thief
RUN pip3 install wheel
RUN pip3 install -r hue-thief/requirements.txt
# for runtime flexibility let's not hard-bake the command into the image
#CMD [ "python3", "hue-thief/hue-thief.py", "/dev/ttyUSB1" ]
```
### build.sh
```
# these files are designed to go into a folder, whose name will be used as the image name
# build an image using the layers described in the Dockerfile
docker build -t $(basename $PWD) .
```
### run.sh
```
# set your device accordingly - might be ttyUSB0 or ttyAMA0
ZHA_DEV=ttyUSB1
# then create the container with the device linked and run the code (removing the container on completion)
docker run --rm --device=/dev/$ZHA_DEV:/dev/$ZHA_DEV -it $(basename $PWD) python hue-thief/hue-thief.py /dev/$ZHA_DEV
# to run diagnostics on the container with a shell use:
# docker run --rm --device=/dev/ttyUSB1:/dev/ttyUSB1 -it $(basename $PWD) bash
```

Put the three files into a new folder on your Docker host – the folder name will be used for the image name. On Linux/MacOS those last two need `chmod +x *.sh` to make them executable, whereas on Windows you might need to adjust the commands or run them manually.  

You simple build it once and run it as many times as you need.
Don't forget that your Docker host needs internet access during the build process to download the Docker base image, this Github repo and the Pip dependencies.


## Problems

I will not be held responsible if you brick any hardware or do other awful things with this. On the bright side: I really don't see how that could ever happen, but still...

This script is kind of a hack, as it tries to implement about a zillion layers of Zigbee protocol in just a few lines of code. :-) So things will only work if everything goes *exactly* according to plan.

If no devices are found, there is no blinking or the factory reset doesn't work, the generated `log.pcap` file should be the first place to look for a clue. (Wireshark has decent Zigbee analyzers, though the ZLL commissioning part is still missing.)

