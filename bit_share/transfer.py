import socket
import struct
import threading
import ipaddress
import psutil
from typing import Optional, Generator, cast
from collections.abc import Iterable

from .types import PacketType
from .packets import Packet


def broadcast_destinations(port: int) -> list[tuple[str, int]]:
    destinations: set[tuple[str, int]] = set()

    for addresses in psutil.net_if_addrs().values():
        primary: tuple[str, int] | None = None
        fallback: tuple[str, int] | None = None

        for address in addresses:
            if address.family != socket.AF_INET:
                continue
            if not address.address or not address.netmask:
                continue
            if address.address.startswith("127."):
                continue

            try:
                iface = ipaddress.IPv4Interface(f"{address.address}/{address.netmask}")
            except ipaddress.AddressValueError:
                continue

            candidate = (str(iface.network.broadcast_address), port)
            if not iface.ip.is_link_local:
                primary = candidate
                break

            if fallback is None:
                fallback = candidate

        selected = primary or fallback
        if selected is not None:
            destinations.add(selected)

    if not destinations:
        destinations.add(("255.255.255.255", port))
    return sorted(destinations)


def _is_udp_destination(value: object) -> bool:
    if not isinstance(value, tuple):
        return False

    value_tuple = cast(tuple[object, ...], value)
    if len(value_tuple) != 2:
        return False

    host = value_tuple[0]
    port = value_tuple[1]

    return isinstance(host, str) and isinstance(port, int)


def _as_udp_destination(value: object) -> tuple[str, int]:
    if not _is_udp_destination(value):
        raise ValueError("Invalid UDP destination")
    return cast(tuple[str, int], value)


def send_packet(
    sock: socket.socket,
    packet: Packet,
    destination: Optional[tuple[str, int] | Iterable[tuple[str, int]]] = None
) -> int:
    
    """Send a framed packet through a socket. Destination required for UDP."""
    # Extract string value from packet type enum and ensure it's exactly 4 bytes
    type_str = packet.type.value
    type_bytes = type_str.encode('utf-8')[:4].ljust(4, b'\x00')
    
    payload = type_bytes + packet.data
    size = len(payload)
    
    frame = struct.pack('!I', size) + payload    
    sock_type = sock.type
    if sock_type == socket.SOCK_DGRAM:
        if destination is None:
            raise ValueError("destination is required for UDP sockets")

        if _is_udp_destination(destination):
            return sock.sendto(frame, _as_udp_destination(destination))

        total_sent = 0
        seen: set[tuple[str, int]] = set()
        for candidate in destination:
            target = _as_udp_destination(candidate)
            if target in seen:
                continue
            seen.add(target)
            try:
                total_sent += sock.sendto(frame, target)
            except OSError:
                continue
        return total_sent
    elif sock_type == socket.SOCK_STREAM:
        return sock.send(frame)
    else:
        raise ValueError(f"Unsupported socket type: {sock_type}")


def recv_packet(
    sock: socket.socket
) -> tuple[Packet, Optional[tuple[str, int]]]:
    """Receive a framed packet from a socket. Returns (packet, address)."""
    sock_type = sock.type
    
    if sock_type == socket.SOCK_DGRAM:
        # UDP: receive entire datagram at once
        data, addr = sock.recvfrom(65535)
        if len(data) < 4:
            raise ValueError("Datagram too small")
        size = struct.unpack('!I', data[:4])[0]
        payload = data[4:4+size]
    elif sock_type == socket.SOCK_STREAM:
        size_data = sock.recv(4)
        if len(size_data) < 4:
            raise ConnectionError("Connection closed or incomplete data")
        size = struct.unpack('!I', size_data)[0]
        
        payload = b''
        remaining = size
        while remaining > 0:
            chunk = sock.recv(remaining)
            if not chunk:
                raise ConnectionError("Connection closed before receiving all data")
            payload += chunk
            remaining -= len(chunk)
        
        addr = None
    else:
        raise ValueError(f"Unsupported socket type: {sock_type}")
    
    type_bytes = payload[:4]
    data = payload[4:]
    
    type_str = type_bytes.decode('utf-8').rstrip('\x00')
    packet_type = PacketType(type_str)
    
    packet = Packet(packet_type, data)
    
    return packet, addr


def next_packet(
    sock: socket.socket,
    stop: Optional[threading.Event] = None
) -> Generator[tuple[Packet, Optional[tuple[str, int]]], None, None]:
    """Generator that continuously yields packets from a socket."""
    while True:
        if stop and stop.is_set():
            break
        try:
            packet, addr = recv_packet(sock)
            yield packet, addr
        except socket.timeout:
            continue
        except (ConnectionError, OSError):
            break


