import argparse
from . import NAME, VERSION, DESCRIPTION, PACKAGE_EXT
from .daemon import Daemon
from .packager import Packager

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

    else:
        parser.print_help()

def main():
    parser = argparse.ArgumentParser(prog=NAME, description=DESCRIPTION)
    
    parser.add_argument('-D', '--daemon', action='store_true', help=f"start {NAME} daemon")
    parser.add_argument('-v', '--version', action='version', version=f"%(prog)s {VERSION}", help="show program's version number and exit")
    
    subparsers = parser.add_subparsers(dest='command', title="available commands") # type: ignore

    create_parser = subparsers.add_parser('create', help="create a bit-share package from a file or directory")
    
    create_parser.add_argument('-s', '--source', type=str, help="path to the source file or directory (defaults to current directory)")
    create_parser.add_argument('-n', '--name', type=str, help="name of the package (defaults to source name)")
    create_parser.add_argument('-o', '--output', type=str, help="path to save the package file (defaults to <name>.json)")  
    
    args = parser.parse_args()

    try:
        __process_args(parser, args)
    except KeyboardInterrupt:
        print("\nExiting... Action interrupted by user.")

if __name__ == '__main__':
    main()