import os
import socket

from .constants import LOCAL_DAEMON_PORT
from .packets import SeedPacket
from .transfer import send_packet
from .package import Package
from .seed import Seed


class API:
	@staticmethod
	def seed(package: Package, path: str | os.PathLike[str]) -> int:
		packet = SeedPacket.from_seed(Seed(package, path))

		with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
			sock.connect(("127.0.0.1", LOCAL_DAEMON_PORT))
			return send_packet(sock, packet)



