import os
import pickle
from typing import Any, cast

from .types import PacketType
from .package import Package
from .seed import Seed

__all__ = ["SeedPacket", "DiscoveryRequestPacket", "DiscoveryResponsePacket"]


def resolve_packet_subclass(packet_type: PacketType) -> type["Packet"]:
    if packet_type == PacketType.SEED:
        return SeedPacket
    if packet_type == PacketType.DISCOVERY_REQUEST:
        return DiscoveryRequestPacket
    if packet_type == PacketType.DISCOVERY_RESPONSE:
        return DiscoveryResponsePacket
    return Packet


class Packet:
    def __init__(self, packet_type: PacketType, data: bytes):
        self._type = packet_type
        self._data = data

        target_cls = resolve_packet_subclass(packet_type)
        if self.__class__ is not target_cls:
            cast(Any, self).__class__ = target_cls
    
    @property
    def type(self):
        return self._type
    
    @property
    def data(self):
        return self._data
    

class SeedPacket(Packet):
    def __init__(self, data: bytes):
        super().__init__(PacketType.SEED, data)

    @classmethod
    def from_seed(cls, seed: Seed) -> "SeedPacket":
        return cls(pickle.dumps(seed))

    @classmethod
    def from_package(cls, package: "Package", path: str | os.PathLike[str]) -> "SeedPacket":
        return cls.from_seed(Seed(package, path))

    @property
    def seed(self) -> Seed:
        payload = pickle.loads(self.data)
        if not isinstance(payload, Seed):
            raise ValueError("Invalid seed packet payload")
        return payload
    

class DiscoveryRequestPacket(Packet):
    def __init__(self, data: bytes):
        super().__init__(PacketType.DISCOVERY_REQUEST, data)

    
    @classmethod
    def from_hash(cls, package_hash: str) -> "DiscoveryRequestPacket":
        return cls(package_hash.encode())
    
    @property
    def hash(self) -> str:
        return self.data.decode()
    
class DiscoveryResponsePacket(Packet):
    def __init__(self, data: bytes):
        super().__init__(PacketType.DISCOVERY_RESPONSE, data)

    @classmethod
    def from_seed(cls, seed: Seed) -> "DiscoveryResponsePacket":
        return cls(seed.package.hash.encode())
    
    @property
    def hash(self) -> str:
        return self.data.decode()