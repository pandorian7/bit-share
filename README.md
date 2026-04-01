```
usage: bit-share [-h] [-D] [-v] {share,shared,discover,download} ...

Simple Torrent Like service to share files in the local network

options:
  -h, --help            show this help message and exit
  -D, --daemon          start bit-share daemon
  -v, --version         show program's version number and exit

available commands:
  {share,shared,discover,download}
    share               share a package to the network
    shared              list packages currently shared by this computer
    discover            discover packages shared by peers on the network
    download            download a package from the network
```