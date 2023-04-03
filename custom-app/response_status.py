# This is a generated file! Please edit source .ksy file and use kaitai-struct-compiler to rebuild

import kaitaistruct
from kaitaistruct import KaitaiStruct, KaitaiStream, BytesIO


if getattr(kaitaistruct, 'API_VERSION', (0, 9)) < (0, 9):
    raise Exception("Incompatible Kaitai Struct Python API: 0.9 or later is required, but you have %s" % (kaitaistruct.__version__))

class ResponseStatus(KaitaiStruct):
    def __init__(self, _io, _parent=None, _root=None):
        self._io = _io
        self._parent = _parent
        self._root = _root if _root else self
        self._read()

    def _read(self):
        self.head = self._io.read_u1()
        self.response_identifier = self._io.read_u1()
        self.unknown1 = self._io.read_u2be()
        self.unknown2 = self._io.read_u2be()
        self.rpm_a = self._io.read_u2be()
        self.rpm_b = self._io.read_u2be()
        self.seconds_moving_over_10 = self._io.read_u2be()
        self.minutes_moving = self._io.read_u2be()
        self.resistance = self._io.read_u1()
        self.unknown3 = self._io.read_u2be()
        self.heart_rate = self._io.read_u2be()
        self.unknown4 = self._io.read_u2be()
        self.unknown5 = self._io.read_u2be()
        self.unknown6 = self._io.read_u2be()
        self.endofmessage = self._io.read_u1()

    def serialize(self):
        output = bytearray()
        output += self.head.to_bytes(1, 'big')
        output += self.response_identifier.to_bytes(1, 'big')
        output += self.unknown1.to_bytes(2, 'big')
        output += self.unknown2.to_bytes(2, 'big')
        output += self.rpm_a.to_bytes(2, 'big')
        output += self.rpm_b.to_bytes(2, 'big')
        output += self.seconds_moving_over_10.to_bytes(2, 'big')
        output += self.minutes_moving.to_bytes(2, 'big')
        output += self.resistance.to_bytes(1, 'big')
        output += self.unknown3.to_bytes(2, 'big')
        output += self.heart_rate.to_bytes(2, 'big')
        output += self.unknown4.to_bytes(2, 'big')
        output += self.unknown5.to_bytes(2, 'big')
        output += self.unknown6.to_bytes(2, 'big')
        output += self.endofmessage.to_bytes(1, 'big')
        return output
