from importlib.metadata import metadata

NAME = "bit-share"
VERSION = metadata(NAME)["Version"]
DESCRIPTION = metadata(NAME)["Summary"]

