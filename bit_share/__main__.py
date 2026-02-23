import argparse

from . import NAME, VERSION, DESCRIPTION
from .daemon import Daemon

def __process_args(parser: argparse.ArgumentParser, args: argparse.Namespace):
    if args.daemon and args.command is not None:
        parser.error("--daemon cannot be combined with subcommands")
    
    if args.daemon:
        daemon = Daemon()
        daemon.start()

    else:
        parser.print_help()

def main():
    parser = argparse.ArgumentParser(prog=NAME, description=DESCRIPTION)
    
    parser.add_argument('-D', '--daemon', action='store_true', help=f"start {NAME} daemon")
    parser.add_argument('-v', '--version', action='version', version=f"%(prog)s {VERSION}", help="show program's version number and exit")
    
    subparsers = parser.add_subparsers(dest='command', title="available commands") # type: ignore

    subparsers.add_parser('create', help="create a bit-share package from a file or directory")
    
    args = parser.parse_args()

    try:
        __process_args(parser, args)
    except KeyboardInterrupt:
        print("\nExiting... Action interrupted by user.")

if __name__ == '__main__':
    main()