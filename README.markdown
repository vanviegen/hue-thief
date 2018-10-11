# Hue Thief


Factory reset Philips Hue bulbs using an EZSP-based Zigbee USB stick. After a reset, bulbs can easily join any type of compatible bridge.


## EZSP-based Zigbee USB sticks

These are devices based on a Silicon Labs EM351 or EM357 chip that communicates with the host PC using the EZSP protocol over a virtual COM port. Which protocol is used depends on which firmware is flashed.

- Silicon Labs/Linear/Nortek/GoControl HubZ/QuickStick Combo (HUSBZB-1). These devices should come with an EZSP firmware preloaded.
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


## Problems

I will not be held responsible if you brick any hardware or do other awful things with this. On the bright side: I really don't see how that could ever happen, but still...

This script is kind of a hack, as it tries to implement about a zillion layers of Zigbee protocol in just a few lines of code. :-) So things will only work if everything goes *exactly* according to plan.

If no devices are found, there is no blinking or the factory reset doesn't work, the generated `log.pcap` file should be the first place to look for a clue. (Wireshark has decent Zigbee analyzers, though the ZLL commissioning part is still missing.)

