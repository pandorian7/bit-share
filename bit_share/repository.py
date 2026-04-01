from .peer import Peer
from .api import API
from .package import Package


class Repository:
    def __init__(self) -> None:
        self.__packages: dict[str, Package] = {}
        self.__peers: dict[str, set[Peer]] = {}

    def discover(self, package_hash: str):
        API.discover_request(package_hash)

    def add_peer(self, package_hash: str, peer_ip: str):
        peers = self.__peers.setdefault(package_hash, set())
        peers.add(Peer(peer_ip, package_hash))

    def find_peers(self, package_hash: str) -> set[Peer] | None:
        return self.__peers.get(package_hash)

    def _await_peers(self, package_hash: str, timeout: float = 30.0) -> set[Peer]:
        import time

        start_time = time.time()
        while time.time() - start_time < timeout:
            peers = self.find_peers(package_hash)
            if peers:
                return peers
            time.sleep(1)
        return set()

    def find_package(self, package_hash: str) -> Package | None:
        if package_hash not in self.__packages:
            if self.find_peers(package_hash) is None:
                
                self.discover(package_hash)
            peers = self._await_peers(package_hash)

            for peer in peers:
                package = API.request_package(package_hash, peer.ip)
                if package:
                    self.__packages[package_hash] = package
                    break

        return self.__packages.get(package_hash)

        
repository = Repository()