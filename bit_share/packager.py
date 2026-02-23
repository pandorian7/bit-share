from functools import cached_property
from pathlib import Path
import math
import os

from .constants import PIECE_SIZE
from .package import Package


class Packager:
    def __init__(self, source: str | os.PathLike[str], name: str | None = None):
        if not os.path.exists(source):
            raise FileNotFoundError(f"source path '{source}' does not exist")
        self.source = Path(source)

        if name is not None:
            self.name = name
        else:
            self.name = self.source.stem

    def is_file(self, path: str | os.PathLike[str] | None = None) -> bool:
        """
        Check if a path points to a file.
        Args:
            path: The path to check. If None, checks the source directory itself.
                  Can be a string or PathLike object.
        Returns:
            bool: True if the path points to a file, False otherwise.
        """

        if path is None:
            return self.source.is_file()
        
        return (self.source.parent / path).is_file()
    
    def is_dir(self, path: str | os.PathLike[str] | None = None) -> bool:
        """
        Check if the given path is a directory.

        Args:
            path: The file system path to check. Can be a string, PathLike object, or None.

        Returns:
            bool: True if the path is a directory, False if it is a file or does not exist.
        """

        path = self.source if path is None else self.source.parent / path

        return path.is_dir() and path.exists()


    @cached_property
    def filelist(self):
        """
        Generate a list of all files in the source directory with their relative paths and sizes.
        Returns:
            list: A list of tuples containing (relative_file_path, file_size) for each file
                  found recursively in the source directory. The relative path is relative to
                  the parent directory of the source path, and file_size is in bytes.
        """

        if self.is_file():
            return [(self.source, self.source.stat().st_size)]

        return [
            (file.relative_to(self.source.parent), file.stat().st_size) for file in self.source.rglob("**/*") if file.is_file()
        ]
    
    def size(self) -> int:
        """
        Calculate the total size of all files in the source directory.
        Returns:
            int: The total size in bytes of all files contained in the source directory.
        """

        return sum(size for _, size in self.filelist)
    
    def piece_count(self) -> int:
        """
        Returns:
            int: Number of pieces in the package
        """

        return math.ceil(self.size() / PIECE_SIZE)
    
    def package(self):

        return Package.from_packager(self)