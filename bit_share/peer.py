
from bit_share.api import API


class Peer:
    def __init__(self, ip: str, package_hash: str):
        self.ip = ip
        self.__hash = package_hash

    @property
    def package(self):
        from .repository import repository
        return repository.find_package(self.__hash)

    def check_file(self, file_index) -> bool:
        return API.file_check(self, file_index)

    def request_file(self, file_index) -> bytes:
        return API.request_file(self, file_index)