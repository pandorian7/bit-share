
from enum import Enum


class PacketType(Enum):
    SEED = "SEED"
    DISCOVERY_REQUEST = "DREQ"
    DISCOVERY_RESPONSE = "DRES"