import os
import socket

from .constants import LOCAL_DAEMON_PORT, REMOTE_DAEMON_PORT, REMOTE_TRANSFER_PORT
from .packets import *
from .packets import PackageRequestPacket
from .packets import PackageResponsePacket
from .packets import DownloadRequestPacket
from .transfer import send_packet, broadcast_destinations
from .package import Package
from .seed import Seed


class API:
	@staticmethod
	def seed(package: Package, path: str | os.PathLike[str]) -> int:
		packet = SeedPacket.from_seed(Seed(package, path))

		with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
			sock.connect(("127.0.0.1", LOCAL_DAEMON_PORT))
			return send_packet(sock, packet)
		
	@staticmethod
	def discover_request(package_hash: str) -> int:
		packet = DiscoveryRequestPacket.from_hash(package_hash)

		with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
			sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
			return send_packet(sock, packet, broadcast_destinations(REMOTE_DAEMON_PORT))
		
	@staticmethod
	def discover_response(seed: Seed, addr: tuple[str, int]) -> int:
		packet = DiscoveryResponsePacket.from_seed(seed)

		with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
			return send_packet(sock, packet, addr, reply=True)

	@staticmethod
	def request_package(package_hash: str, ip: str):
		packet = PackageRequestPacket.from_hash(package_hash)
		with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
			sock.connect((ip, REMOTE_TRANSFER_PORT))
			res, _ = send_packet(sock, packet)
			
			if isinstance(res, PackageResponsePacket):
				return res.package

	@staticmethod
	def download_package(package_hash: str, destination: str | os.PathLike[str]) -> None:
		packet = DownloadRequestPacket(package_hash, destination)

		with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
			sock.connect(("127.0.0.1", LOCAL_DAEMON_PORT))
			return send_packet(sock, packet)
