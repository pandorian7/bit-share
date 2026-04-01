from builtins import staticmethod
import typing

from .packets import FileRequestPacket, FileResponsePacket

if typing.TYPE_CHECKING:
	from bit_share.peer import Peer


import os
import socket
import time

from .constants import LOCAL_DAEMON_PORT, REMOTE_DAEMON_PORT, REMOTE_TRANSFER_PORT
from .packets import *
from .packets import PackageRequestPacket
from .packets import PackageResponsePacket
from .packets import DownloadRequestPacket
from .packets import FileCheckPacket
from .packets import FileCheckResponsePacket
from .transfer import send_packet, broadcast_destinations, recv_packet
from .package import Package
from .discovery import DiscoveryBox
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
	def discover_list_response(items: list[dict[str, typing.Any]], addr: tuple[str, int]) -> int:
		packet = DiscoveryListResponsePacket.from_items(items)

		with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
			return send_packet(sock, packet, addr, reply=True)

	@staticmethod
	def discover_shared(timeout: float = 3.0) -> list[dict[str, typing.Any]]:
		packet = DiscoveryListRequestPacket()
		box = DiscoveryBox()

		with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
			sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
			sock.bind(("", 0))
			send_packet(sock, packet, broadcast_destinations(REMOTE_DAEMON_PORT), reply=True)

			deadline = time.monotonic() + max(0.0, timeout)
			while True:
				remaining = deadline - time.monotonic()
				if remaining <= 0:
					break

				sock.settimeout(min(0.2, remaining))
				try:
					res, addr = recv_packet(sock)
				except socket.timeout:
					continue

				if isinstance(res, DiscoveryListResponsePacket) and addr:
					box.add(addr[0], res.items)

		return box.items()

	@staticmethod
	def request_package(package_hash: str, ip: str):
		packet = PackageRequestPacket.from_hash(package_hash)
		with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
			sock.connect((ip, REMOTE_TRANSFER_PORT))
			res, _ = send_packet(sock, packet)
			
			if isinstance(res, PackageResponsePacket):
				return res.package

	@staticmethod
	def download_package(package_hash: str, destination: str | os.PathLike[str]) -> str:
		packet = DownloadRequestPacket(package_hash, destination)

		with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
			sock.connect(("127.0.0.1", LOCAL_DAEMON_PORT))
			res, _ = send_packet(sock, packet)
			if isinstance(res, DownloadResponsePacket):
				return res.job_id
			raise RuntimeError("Daemon did not return a valid download job response")

	@staticmethod
	def download_status(job_id: str) -> dict[str, typing.Any]:
		packet = DownloadStatusRequestPacket.from_job_id(job_id)

		with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
			sock.connect(("127.0.0.1", LOCAL_DAEMON_PORT))
			res, _ = send_packet(sock, packet)
			if isinstance(res, DownloadStatusResponsePacket):
				return res.status
			raise RuntimeError("Daemon did not return a valid download status response")

	@staticmethod
	def shared_list() -> list[dict[str, typing.Any]]:
		packet = SharedListRequestPacket()

		with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
			sock.connect(("127.0.0.1", LOCAL_DAEMON_PORT))
			res, _ = send_packet(sock, packet)
			if isinstance(res, SharedListResponsePacket):
				return res.items
			raise RuntimeError("Daemon did not return a valid shared list response")

	@staticmethod
	def file_check(perr: "Peer", file_index: int) -> bool:
		packet = FileCheckPacket(perr.package.hash, file_index)

		with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
			sock.connect((perr.ip, REMOTE_TRANSFER_PORT))
			res, _ = send_packet(sock, packet)

			if isinstance(res, FileCheckResponsePacket):
				return res.exists
	
	@staticmethod
	def request_file(perr: "Peer", file_index: int) -> bytes:
		packet = FileRequestPacket(perr.package.hash, file_index)

		with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
			sock.connect((perr.ip, REMOTE_TRANSFER_PORT))
			res, _ = send_packet(sock, packet)

			if isinstance(res, FileResponsePacket):
				return res.content