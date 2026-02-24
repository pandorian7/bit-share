from .types import PacketType

class Packet:
    def __init__(self, packet_type: PacketType, data: bytes):
        self._type = packet_type
        self._data = data
    
    @property
    def type(self):
        return self._type
    
    @property
    def data(self):
        return self._data
    
