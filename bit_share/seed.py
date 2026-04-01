import hashlib

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


    def verify_file(self, file_index: int) -> bool:
        if file_index < 0 or file_index >= len(self.package.filelist):
            raise IndexError("file index out of range")
        
        path, size, hash = self.package.filelist[file_index]
        file_path = self.path.absolute() / path
        if not file_path.exists() or not file_path.is_file():
            return False
        
        if file_path.stat().st_size != size:
            return False
        
        with open(file_path, "rb") as f:
            content = f.read()
            return hashlib.md5(content).hexdigest() == hash

    def read_file(self, file_index: int) -> bytes:
        if file_index < 0 or file_index >= len(self.package.filelist):
            raise IndexError("file index out of range")
        
        path, size, hash = self.package.filelist[file_index]
        file_path = self.path.absolute() / path
        if not file_path.exists() or not file_path.is_file():
            raise FileNotFoundError(f"file '{file_path}' does not exist")
        
        with open(file_path, "rb") as f:
            content = f.read()
            if hashlib.md5(content).hexdigest() != hash:
                raise ValueError(f"file '{file_path}' is corrupted")
            return content 