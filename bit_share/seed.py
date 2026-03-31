import os
from pathlib import Path

from .package import Package


class Seed:
    def __init__(self, package: Package, path: str | os.PathLike[str]):
        self._package = package
        self._path = os.fspath(path)

    @property
    def package(self) -> Package:
        return self._package

    @property
    def path(self):
        return Path(self._path)
