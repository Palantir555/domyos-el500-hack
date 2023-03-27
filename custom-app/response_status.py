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
        self.end_of_message_byte = self._io.read_u1()

    def __str__(self):
        return str(f"head: {self.head}, response_identifier: {self.response_identifier}, unknown1: {self.unknown1}, unknown2: {self.unknown2}, rpm_a: {self.rpm_a}, rpm_b: {self.rpm_b}, seconds_moving_over_10: {self.seconds_moving_over_10}, minutes_moving: {self.minutes_moving}, resistance: {self.resistance}, unknown3: {self.unknown3}, heart_rate: {self.heart_rate}, end_of_message_byte: {self.end_of_message_byte}")
