from typing import Any


class DiscoveryBox:
    def __init__(self) -> None:
        self._items: dict[tuple[str, str], dict[str, Any]] = {}

    def add(self, peer_ip: str, packages: list[dict[str, Any]]) -> None:
        for package in packages:
            package_hash = str(package.get("hash", ""))
            if not package_hash:
                continue

            files_value = package.get("files", 0)
            try:
                files_count = int(files_value)
            except (TypeError, ValueError):
                files_count = 0

            key = (peer_ip, package_hash)
            self._items[key] = {
                "peer": peer_ip,
                "name": str(package.get("name", "")),
                "files": files_count,
                "hash": package_hash,
            }

    def items(self) -> list[dict[str, Any]]:
        return sorted(
            self._items.values(),
            key=lambda item: (str(item["peer"]), str(item["name"]), str(item["hash"])),
        )