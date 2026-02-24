from __future__ import annotations

import signal
import socket
import threading
from abc import ABC, abstractmethod
from types import FrameType
from typing import Callable


from .constants import LOCAL_DAEMON_PORT, REMOTE_DAEMON_PORT, REMOTE_TRANSFER_PORT
from .transfer import next_packet
from .seedbox import SeedBox
from .packets import Packet
from .packets import *


class DaemonBase(ABC):
    """Base class providing generic server infrastructure."""
    
    def __init__(self):
        self._stop_event = threading.Event()
        self.seed_box = SeedBox()

    @abstractmethod
    def _remote_daemon_server(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def _remote_transfer_server(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def _local_daemon_server(self) -> None:
        raise NotImplementedError

    def start(self) -> None:
        self._stop_event.clear()

        threads = [
            threading.Thread(target=self._remote_daemon_server, name="remote-daemon-server"),
            threading.Thread(target=self._remote_transfer_server, name="remote-transfer-server"),
            threading.Thread(target=self._local_daemon_server, name="local-daemon-server"),
        ]

        def _handle_sigint(_signum: int, _frame: FrameType | None) -> None:
            print("Server is shutting down...")
            self.stop()

        previous_sigint_handler = signal.getsignal(signal.SIGINT)
        signal.signal(signal.SIGINT, _handle_sigint)

        try:
            for thread in threads:
                thread.start()

            while any(thread.is_alive() for thread in threads):
                for thread in threads:
                    thread.join(timeout=0.2)
                if self._stop_event.is_set():
                    break
        finally:
            self.stop()
            for thread in threads:
                thread.join(timeout=1.0)
            signal.signal(signal.SIGINT, previous_sigint_handler)

    def stop(self) -> None:
        """Signal all servers to stop."""
        self._stop_event.set()

    def _close_socket(self, sock: socket.socket) -> None:
        """Safely close a socket, ignoring errors."""
        try:
            sock.close()
        except OSError:
            pass

    def _run_udp_server(
        self,
        port: int,
        handler: Callable[[Packet, tuple[str, int]], None]
    ) -> None:
        """Generic UDP server that receives packets and calls handler."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(("", port))
        sock.settimeout(0.5)

        try:
            for packet, addr in next_packet(sock, self._stop_event):
                if addr:
                    handler(packet, addr)
        finally:
            self._close_socket(sock)

    def _run_tcp_server(
        self,
        host: str,
        port: int,
        handler: Callable[[Packet, tuple[str, int]], None]
    ) -> None:
        """Generic TCP server that accepts connections and receives packets."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((host, port))
        sock.listen()
        sock.settimeout(0.5)

        try:
            while not self._stop_event.is_set():
                try:
                    conn, addr = sock.accept()
                except socket.timeout:
                    continue
                except OSError:
                    break

                try:
                    # Use addr from accept(), not from next_packet (which returns None for TCP)
                    for packet, _ in next_packet(conn, self._stop_event):
                        handler(packet, addr)
                finally:
                    self._close_socket(conn)
        finally:
            self._close_socket(sock)


class Daemon(DaemonBase):
    """Application-specific daemon with three server endpoints."""
    
    def __init__(self):
        super().__init__()

    def _remote_daemon_server(self) -> None:
        print(f"Remote daemon server (UDP) listening on 0.0.0.0:{REMOTE_DAEMON_PORT}")
        
        def handler(packet: Packet, addr: tuple[str, int]) -> None:
            print(f"[remote-daemon/UDP] Received from {addr[0]}:{addr[1]} | type={packet.type.value} | size={len(packet.data)} bytes")

        self._run_udp_server(REMOTE_DAEMON_PORT, handler)

    def _remote_transfer_server(self) -> None:
        print(f"Remote transfer server (TCP) listening on 0.0.0.0:{REMOTE_TRANSFER_PORT}")
        
        def handler(packet: Packet, addr: tuple[str, int]) -> None:
            print(f"[remote-transfer/TCP] Received from {addr[0]}:{addr[1]} | type={packet.type.value} | size={len(packet.data)} bytes")

        self._run_tcp_server("", REMOTE_TRANSFER_PORT, handler)

    def _local_daemon_server(self) -> None:
        print(f"Local daemon server (TCP) listening on 127.0.0.1:{LOCAL_DAEMON_PORT}")
        
        def handler(packet: Packet, addr: tuple[str, int]) -> None:
            if isinstance(packet, SeedPacket):
                print(f"[LOCAL/SEED] hash={packet.seed.package.hash} | path={packet.seed.path}")
                self.seed_box.add(packet.seed)

        self._run_tcp_server("127.0.0.1", LOCAL_DAEMON_PORT, handler)