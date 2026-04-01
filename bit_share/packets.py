import os
from pathlib import Path
import pickle
from typing import Any, cast

from .types import PacketType
from .package import Package
from .seed import Seed

__all__ = [
    "Packet",
    "SeedPacket",
    "DiscoveryRequestPacket",
    "DiscoveryResponsePacket",
    "PackageRequestPacket",
    "PackageResponsePacket",
    "DownloadRequestPacket",
    "DownloadResponsePacket",
    "DownloadStatusRequestPacket",
    "DownloadStatusResponsePacket",
    "SharedListRequestPacket",
    "SharedListResponsePacket",
    "FileCheckPacket",
    "FileCheckResponsePacket",
    "FileRequestPacket",
    "FileResponsePacket",
    "EmptyPacket",
]


def resolve_packet_subclass(packet_type: PacketType) -> type["Packet"]:
    if packet_type == PacketType.SEED:
        return SeedPacket
    if packet_type == PacketType.DISCOVERY_REQUEST:
        return DiscoveryRequestPacket
    if packet_type == PacketType.DISCOVERY_RESPONSE:
        return DiscoveryResponsePacket
    if packet_type == PacketType.PACKAGE_REQUEST:
        return PackageRequestPacket
    if packet_type == PacketType.PACKAGE_RESPONSE:
        return PackageResponsePacket
    if packet_type == PacketType.DOWNLOAD_REQUEST:
        return DownloadRequestPacket
    if packet_type == PacketType.DOWNLOAD_RESPONSE:
        return DownloadResponsePacket
    if packet_type == PacketType.DOWNLOAD_STATUS_REQUEST:
        return DownloadStatusRequestPacket
    if packet_type == PacketType.DOWNLOAD_STATUS_RESPONSE:
        return DownloadStatusResponsePacket
    if packet_type == PacketType.SHARED_LIST_REQUEST:
        return SharedListRequestPacket
    if packet_type == PacketType.SHARED_LIST_RESPONSE:
        return SharedListResponsePacket
    if packet_type == PacketType.FILE_CHECK_REQUEST:
        return FileCheckPacket
    if packet_type == PacketType.FILE_CHECK_RESPONSE:
        return FileCheckResponsePacket
    if packet_type == PacketType.FILE_REQUEST:
        return FileRequestPacket
    if packet_type == PacketType.FILE_RESPONSE:
        return FileResponsePacket
    if packet_type == PacketType.EMPTY:
        return EmptyPacket
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

class PackageRequestPacket(Packet):
    def __init__(self, data: bytes):
        super().__init__(PacketType.PACKAGE_REQUEST, data)

    @classmethod
    def from_hash(cls, package_hash: str) -> "PackageRequestPacket":
        return cls(package_hash.encode())
    
    @property
    def hash(self) -> str:
        return self.data.decode()

class PackageResponsePacket(Packet):
    def __init__(self, data: bytes):
        super().__init__(PacketType.PACKAGE_RESPONSE, data)

    @classmethod
    def from_package(cls, package: Package) -> "PackageResponsePacket":
        return cls(package.encode())
    
    @property
    def package(self) -> Package:
        payload = pickle.loads(self.data)
        if not isinstance(payload, Package):
            raise ValueError("Invalid package response packet payload")
        return payload

class DownloadRequestPacket(Packet):
    def __init__(self, hash: str, destination: str | os.PathLike[str]):
        
        data = f"{hash}:{os.path.abspath(destination)}".encode()
        super().__init__(PacketType.DOWNLOAD_REQUEST, data)

    @property
    def hash(self) -> str:
        return self.data.decode().split(":", 1)[0]
    

    @property
    def destination(self) -> Path:
        return Path(self.data.decode().split(":", 1)[1]).absolute()


class DownloadResponsePacket(Packet):
    def __init__(self, data: bytes):
        super().__init__(PacketType.DOWNLOAD_RESPONSE, data)

    @classmethod
    def from_job_id(cls, job_id: str) -> "DownloadResponsePacket":
        return cls(job_id.encode())

    @property
    def job_id(self) -> str:
        return self.data.decode()


class DownloadStatusRequestPacket(Packet):
    def __init__(self, data: bytes):
        super().__init__(PacketType.DOWNLOAD_STATUS_REQUEST, data)

    @classmethod
    def from_job_id(cls, job_id: str) -> "DownloadStatusRequestPacket":
        return cls(job_id.encode())

    @property
    def job_id(self) -> str:
        return self.data.decode()


class DownloadStatusResponsePacket(Packet):
    def __init__(self, data: bytes):
        super().__init__(PacketType.DOWNLOAD_STATUS_RESPONSE, data)

    @classmethod
    def from_status(cls, status: dict[str, Any]) -> "DownloadStatusResponsePacket":
        return cls(pickle.dumps(status))

    @property
    def status(self) -> dict[str, Any]:
        payload = pickle.loads(self.data)
        if not isinstance(payload, dict):
            raise ValueError("Invalid download status packet payload")
        return payload


class SharedListRequestPacket(Packet):
    def __init__(self):
        super().__init__(PacketType.SHARED_LIST_REQUEST, b"list")


class SharedListResponsePacket(Packet):
    def __init__(self, data: bytes):
        super().__init__(PacketType.SHARED_LIST_RESPONSE, data)

    @classmethod
    def from_items(cls, items: list[dict[str, Any]]) -> "SharedListResponsePacket":
        return cls(pickle.dumps(items))

    @property
    def items(self) -> list[dict[str, Any]]:
        payload = pickle.loads(self.data)
        if not isinstance(payload, list):
            raise ValueError("Invalid shared list packet payload")
        return payload

class FileCheckPacket(Packet):
    def __init__(self, package_hash: str, file_index: int):
        data = f"{package_hash}:{file_index}".encode()
        super().__init__(PacketType.FILE_CHECK_REQUEST, data)

    @property
    def package_hash(self) -> str:
        return self.data.decode().split(":", 1)[0]

    @property
    def file_index(self) -> int:
        return int(self.data.decode().split(":", 1)[1])
    
class FileCheckResponsePacket(Packet):
    def __init__(self, exists: bool):
        data = b"1" if exists else b"0"
        super().__init__(PacketType.FILE_CHECK_RESPONSE, data)

    @property
    def exists(self) -> bool:
        return self.data == b"1"   

class FileRequestPacket(Packet):
    def __init__(self, package_hash: str, file_index: int):
        data = f"{package_hash}:{file_index}".encode()
        super().__init__(PacketType.FILE_REQUEST, data)

    @property
    def package_hash(self) -> str:
        return self.data.decode().split(":", 1)[0]

    @property
    def file_index(self) -> int:
        return int(self.data.decode().split(":", 1)[1])
    
class FileResponsePacket(Packet):
    def __init__(self, package_hash: str, file_index: int, content: bytes):
        data = f"{package_hash}:{file_index}:".encode() + content
        super().__init__(PacketType.FILE_RESPONSE, data)

    @property
    def package_hash(self) -> str:
        return self.data.decode().split(":", 2)[0]

    @property
    def file_index(self) -> int:
        return int(self.data.decode().split(":", 2)[1])
    
    @property
    def content(self) -> bytes:
        return self.data.split(b":", 2)[2]

class EmptyPacket(Packet):
    def __init__(self):
        super().__init__(PacketType.EMPTY, b"no_data")
    