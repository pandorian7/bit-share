from .seed import Seed


class SeedBox:
	def __init__(self):
		self._by_hash: dict[str, Seed] = {}

	def add(self, seed: Seed) -> None:
		package_hash = seed.package.hash
		self._by_hash[package_hash] = seed

	def lookup(self, package_hash: str) -> Seed | None:
		return self._by_hash.get(package_hash)
