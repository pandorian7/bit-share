import argparse
from pathlib import Path
from . import NAME, VERSION, DESCRIPTION
from .constants import PACKAGE_EXT
from .daemon import Daemon
from .packager import Packager
from .package import Package
from .api import API

import os

def __process_args(parser: argparse.ArgumentParser, args: argparse.Namespace):
    if args.daemon and args.command is not None:
        parser.error("--daemon cannot be combined with subcommands")
    
    if args.daemon:
        daemon = Daemon()
        daemon.start()

    if args.command == "create":

        source = args.source or os.getcwd()

        packager = Packager(source=source, name=args.name)

        if args.output is None:
            if packager.is_file():
                output = f"{packager.source.stem}.{PACKAGE_EXT}"
            else:
                output = f"{packager.name}.{PACKAGE_EXT}"
        else: 
            output = args.output
        
        package = packager.package()
        package.save(output)

        print(f"Package was written to '{output}'")

    if args.command == "share":
        # assert isinstance(args.package, Path), "package argument must be a Path object"
        assert isinstance(args.path, Path), "path argument must be a Path object"

        packager = Packager(source=args.path)
        package = packager.package()

        print(f"Sharing package with {len(package.filelist)} files...")
        print(f"Package hash: {package.hash}")
        API.seed(package, args.path)

    if args.command == "download":
        try:
            package = API.download_package(args.hash, args.destination)
            print(f"Package downloaded to '{args.destination}'")
        except Exception as e:
            print(f"Error downloading package: {e}")
def main():
    parser = argparse.ArgumentParser(prog=NAME, description=DESCRIPTION)
    
    parser.add_argument('-D', '--daemon', action='store_true', help=f"start {NAME} daemon")
    parser.add_argument('-v', '--version', action='version', version=f"%(prog)s {VERSION}", help="show program's version number and exit")
    
    subparsers = parser.add_subparsers(dest='command', title="available commands") # type: ignore

    # create_parser = subparsers.add_parser('create', help="create a bit-share package from a file or directory")
    # create_parser.add_argument('-s', '--source', type=str, help="path to the source file or directory (defaults to current directory)")
    # create_parser.add_argument('-n', '--name', type=str, help="name of the package (defaults to source name)")
    # create_parser.add_argument('-o', '--output', type=str, help="path to save the package file (defaults to <name>.json)")  

    share_parser = subparsers.add_parser('share', help="share a package to the network")
    share_parser.add_argument('path', type=Path, help="local path to share for this package")

    download_parser = subparsers.add_parser('download', help="download a package from the network")
    download_parser.add_argument('hash', type=str, help="hash of the package to download")
    download_parser.add_argument('destination', type=Path, help="local path to save the downloaded package")

    args = parser.parse_args()

    try:
        __process_args(parser, args)
    except KeyboardInterrupt:
        print("\nExiting... Action interrupted by user.")

if __name__ == '__main__':
    main()