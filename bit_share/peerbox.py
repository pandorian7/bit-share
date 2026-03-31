class PeerBox:
	def __init__(self):
		self._by_hash: dict[str, set[str]] = {}

	def add(self, package_hash: str, peer_ip: str) -> None:
		peers = self._by_hash.setdefault(package_hash, set())
		peers.add(peer_ip)

	def lookup(self, package_hash: str) -> set[str]:
		return set(self._by_hash.get(package_hash, set()))

	def await_peers(self, package_hash: str, timeout: float = 30.0) -> set[str]:
		import time

		start_time = time.time()
		while time.time() - start_time < timeout:
			peers = self.lookup(package_hash)
			if peers:
				return peers
			time.sleep(1)
		return set()