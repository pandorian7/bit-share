import argparse
from pathlib import Path
import time
from . import NAME, VERSION, DESCRIPTION
from .constants import PACKAGE_EXT
from .daemon import Daemon
from .packager import Packager
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

        packager = Packager(source=args.path, name=args.name)
        package = packager.package()

        print(f"Sharing package with {len(package.filelist)} files...")
        print(f"Package hash: {package.hash}")
        API.seed(package, args.path.absolute())

    if args.command == "shared":
        try:
            items = API.shared_list()
            if not items:
                print("No packages are currently being shared.")
                return

            headers = ["#", "Name", "Files", "Hash", "Path"]
            rows = [
                [
                    str(index),
                    str(item.get("name", "")),
                    str(item.get("files", "")),
                    str(item.get("hash", "")),
                    str(item.get("path", "")),
                ]
                for index, item in enumerate(items, start=1)
            ]

            widths = [len(header) for header in headers]
            for row in rows:
                for i, cell in enumerate(row):
                    widths[i] = max(widths[i], len(cell))

            def _fmt(row: list[str]) -> str:
                return " | ".join(cell.ljust(widths[i]) for i, cell in enumerate(row))

            print(_fmt(headers))
            print("-+-".join("-" * width for width in widths))
            for row in rows:
                print(_fmt(row))
        except Exception as e:
            print(f"Error reading shared packages: {e}")

    if args.command == "download":
        try:
            job_id = API.download_package(args.hash, args.destination)
            print(f"Download job started: {job_id}")

            last_progress: tuple[object, ...] | None = None
            last_render_len = 0
            while True:
                status = API.download_status(job_id)
                completed_files = status.get("completed_files", 0)
                total_files = status.get("total_files", 0)
                current_file = status.get("current_file") or "waiting..."
                status_name = status.get("status", "UNKNOWN")
                skipped_files = status.get("skipped_files", [])
                error = status.get("error")

                progress_key = (
                    completed_files,
                    total_files,
                    current_file,
                    status_name,
                    len(skipped_files) if isinstance(skipped_files, list) else 0,
                    error,
                )
                if progress_key != last_progress:
                    progress_line = f"({completed_files}/{total_files}) {current_file} [{status_name}]"
                    extra_padding = " " * max(0, last_render_len - len(progress_line))
                    print(f"\r{progress_line}{extra_padding}", end="", flush=True)
                    last_render_len = len(progress_line)
                    last_progress = progress_key

                if status.get("done"):
                    print()
                    if status_name == "FAILED":
                        print(f"Download failed: {error}")
                    else:
                        print(f"Download finished to '{args.destination.absolute()}'")
                        if isinstance(skipped_files, list) and skipped_files:
                            print("Skipped files:")
                            for skipped in skipped_files:
                                print(f"- {skipped}")
                    break

                time.sleep(0.5)
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
    share_parser.add_argument('-n', '--name', type=str, default=None, help="override package name (defaults to file/folder name)")

    subparsers.add_parser('shared', help="list packages currently shared by this computer")

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