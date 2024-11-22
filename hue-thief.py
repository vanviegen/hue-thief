import asyncio
import pure_pcapy
import time
import sys
import argparse

from random import randint

import bellows
import bellows.cli.util as util
import interpanZll


class Prompt:
    def __init__(self):
        self.q = asyncio.Queue()
        asyncio.get_event_loop().add_reader(sys.stdin, self.got_input)

    def got_input(self):
        asyncio.ensure_future(self.q.put(sys.stdin.readline()))

    async def __call__(self, msg, end='\n', flush=False):
        print(msg, end=end, flush=flush)
        return (await self.q.get()).rstrip('\n')


async def steal(device_path, baudrate, scan_channel):
    dev = await util.setup(device_path, baudrate)
    eui64 = await getattr(dev, 'getEui64')()
    eui64 = bellows.types.named.EmberEUI64(*eui64)

    res = await dev.mfglibStart(True)
    util.check(res[0], "Unable to start mfglib")

    DLT_IEEE802_15_4 = 195
    pcap = pure_pcapy.Dumper("log.pcap", 128, DLT_IEEE802_15_4)
    prompt = Prompt()


    def dump_pcap(frame):
        frame = bytes(frame)
        ts = time.time()
        ts_sec = int(ts)
        ts_usec = int((ts - ts_sec) * 1000000)
        hdr = pure_pcapy.Pkthdr(ts_sec, ts_usec, len(frame), len(frame))
        pcap.dump(hdr, frame)


    def handle_incoming(frame_name, response):
        if frame_name != "mfglibRxHandler":
            return

        data = response[2]
        dump_pcap(data)

        if len(data)<10: # Not sure what this is, but not a proper response
            return

        try:
            resp = interpanZll.ScanResp.deserialize(data)[0]
        except ValueError:
            return
        if resp.transactionId != transaction_id: # Not for us
            return

        targets.add(resp.extSrc)
        frame = interpanZll.AckFrame(seq = resp.seq).serialize()
        dump_pcap(frame)
        asyncio.create_task(dev.mfglibSendPacket(frame))

    cbid = dev.add_callback(handle_incoming)


    for channel in ([scan_channel] if scan_channel else range(11, 27)):
        print("Scanning on channel",channel)
        res = await dev.mfglibSetChannel(channel)
        util.check(res[0], "Unable to set channel")

        transaction_id = randint(0, 0xFFFFFFFF)
        targets = set()

        # https://www.nxp.com/docs/en/user-guide/JN-UG-3091.pdf section 6.8.5
        frame = interpanZll.ScanReq(
            seq = 1,
            srcPan = 0,
            extSrc = eui64,
            transactionId = transaction_id,
        ).serialize()
        dump_pcap(frame)
        res = await dev.mfglibSendPacket(frame)
        util.check(res[0], "Unable to send packet")

        await asyncio.sleep(1)

        while len(targets)>0:
            target = targets.pop()
            frame = interpanZll.IdentifyReq(
                seq = 2,
                srcPan = 0,
                extSrc = eui64,
                transactionId = transaction_id,
                extDst = target,
                frameControl = 0xCC21,
            ).serialize()
            dump_pcap(frame)
            await dev.mfglibSendPacket(frame)
            answer = await prompt("Do you want to factory reset the light that just blinked? [y|n] ")

            if answer.strip().lower() == "y":
                print("Factory resetting "+str(target))
                frame = interpanZll.FactoryResetReq(
                    seq = 3,
                    srcPan = 0,
                    extSrc = eui64,
                    transactionId = transaction_id,
                    extDst = target,
                    frameControl = 0xCC21,
                ).serialize()
                dump_pcap(frame)
                await dev.mfglibSendPacket(frame)
                await asyncio.sleep(1)

    dev.remove_callback(cbid)

    await dev.mfglibEnd()

    await dev.disconnect()


parser = argparse.ArgumentParser(description='Factory reset a Hue light bulb.')
parser.add_argument('device', type=str, help='Device path, e.g., /dev/ttyUSB0')
parser.add_argument('-b', '--baudrate', type=int, default=57600, help='Baud rate (default: 57600)')
parser.add_argument('-c', '--channel', type=int, help='Zigbee channel (defaults to scanning 11 up to 26)')
args = parser.parse_args()

asyncio.get_event_loop().run_until_complete(steal(args.device, args.baudrate, args.channel))
