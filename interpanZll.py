from bellows.types import basic
from bellows.types import named


class EzspStruct:
    def __init__(self, *args, **kwargs):
        if len(args) == 1 and isinstance(args[0], self.__class__):
            # copy constructor
            for field in self._fields:
                self.set(field[0], getattr(args[0], field[0]))
        else:
            # set positional arguments
            for n,val in enumerate(args):
                self.set(self._fields[n][0], val)
            # set named arguments
            for name,val in kwargs.items():
                self.set(name, val)
        # set default values
        for field in self._fields:
            if len(field)>=3 and getattr(self, field[0], None) == None:
                self.set(field[0], field[2])

    def set(self, name, val):
        for field in self._fields:
            if field[0] == name:
                setattr(self, name, field[1](val))
                return
        raise Exception("no such field "+name)
     
    def serialize(self):
        r = b''
        for field in self._fields:
            r += getattr(self, field[0]).serialize()
        return r

    @classmethod
    def deserialize(cls, data):
        r = cls()
        for field in cls._fields:
            v, data = field[1].deserialize(data)
            setattr(r, field[0], v)
        return r, data

    def __repr__(self):
        r = '<%s ' % (self.__class__.__name__, )
        r += ' '.join(
            ['%s=%s' % (f[0], getattr(self, f[0], None)) for f in self._fields]
        )
        r += '>'
        return r


def zllInterpanFields(command = None, fields = [], broadcast = False):
    if broadcast:
        dst = ('dst', basic.uint16_t, 0xFFFF)
    else:
        dst = ('extDst', named.EmberEUI64)
    return [
        # 802.15.4:
        ('frameControl', basic.uint16_t, 0xC801 if broadcast else 0xCC01),
        ('seq', basic.uint8_t),
        ('dstPan', basic.uint16_t, 0xffff),
        dst,
        ('srcPan', basic.uint16_t),
        ('extSrc', named.EmberEUI64),
        # network layer:
        ('networkLayerFrameControl', basic.uint16_t, 0x000b),
        # application support layer:
        ('supportLayerFrameControl', basic.uint8_t, 0x0b if broadcast else 0x03),
        ('cluster', basic.uint16_t, 0x1000),
        ('profile', basic.uint16_t, 0xc05e),
        # cluster library frame
        ('clusterLibraryFrameControl', basic.uint8_t, 0x11),
        ('clusterLibrarySeq', basic.uint8_t, 0),
        ('command', basic.uint8_t, command),
    ] + fields + [
        ('crc', basic.uint16_t, 0x116A), # set by the device firmware
    ]    

class AckFrame(EzspStruct):
    _fields = [
        ('frameControl', basic.uint16_t, 0x0002),
        ('seq', basic.uint8_t),
   ]

class ScanReq(EzspStruct):
    _fields = zllInterpanFields(
        command = 0,
        fields = [
            ('transactionId', basic.uint32_t),
            ('zigbeeInfo', basic.uint8_t, 0x05),
            ('zllInfo', basic.uint8_t, 0x12),
        ],
        broadcast = True,
    )


class IdentifyReq(EzspStruct):
    _fields = zllInterpanFields(
        command = 0x6,
        fields = [
            ('transactionId', basic.uint32_t),
            ('duration', basic.uint16_t, 0xFFFF),
        ],
    )
    
class FactoryResetReq(EzspStruct):
    _fields = zllInterpanFields(
        command = 0x7,
        fields = [
            ('transactionId', basic.uint32_t),
        ],
    )


class ScanReq(EzspStruct):
    _fields = zllInterpanFields(
        command = 0,
        fields = [
            ('transactionId', basic.uint32_t),
            ('zigbeeInfo', basic.uint8_t, 0x05),
            ('zllInfo', basic.uint8_t, 0x12),
        ],
        broadcast = True,
    )

class ScanResp(EzspStruct):
    _fields = zllInterpanFields(
        command = 1,
        fields = [
            ('transactionId', basic.uint32_t),
            ('rSSICorrection', basic.uint8_t),
            ('zigbeeInfo', basic.uint8_t),
            ('zllInfo', basic.uint8_t),
            ('keyMask', basic.uint16_t),
            ('responseId', basic.uint32_t),
            ('extPanId', basic.uint64_t),
            ('nwkUpdateId', basic.uint8_t),
            ('logicalChannel', basic.uint8_t),
            ('panId', basic.uint16_t),
            ('nwkAddr', basic.uint16_t),
            ('numberSubDevices', basic.uint8_t),
            ('totalGroupIds', basic.uint8_t),
            ('endpoint', basic.uint8_t),
            ('profileId', basic.uint16_t),
            ('deviceId', basic.uint16_t),
            ('version', basic.uint8_t),
            ('groupIdCount', basic.uint8_t),
        ],
    )

