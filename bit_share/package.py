from functools import cached_property

from .packager import Packager
import hashlib
import json
import os

class Package:
    name: str
    filelist: list[tuple[str, int]]
    header_hash: str

    def __init__(self, name: str, filelist: list[tuple[str, int]]):
        self.name = name
        self.filelist = filelist

    @classmethod
    def from_packager(cls, packager: Packager) -> "Package":
        return cls(
            name=packager.name,
            filelist=sorted([(path.as_posix(), size) for path, size in packager.filelist], key=lambda x: x[0])
        )
    
    @classmethod
    def from_file(cls, path: str | os.PathLike[str]) -> "Package":
        with open(path, "r") as file:
            data = json.load(file)
            ret = cls(
                name=data["name"],
                filelist=data["filelist"]
            )

            if ret.hash != data["hash"]:
                raise ValueError("Hash mismatch: package file may be corrupted")

            return ret
    
    @cached_property
    def hash(self) -> str:
        content = f"{self.name}:{''.join(f'{path}:{size}' for path, size in self.filelist)}"
        return hashlib.sha256(content.encode()).hexdigest()
    
    def save(self, path: str | os.PathLike[str]) -> None:
        with open(path, "w") as file:
            json.dump({
                "name": self.name,
                "filelist": self.filelist,
                "hash": self.hash
            }, file)
        

