import enum
from pathlib import Path
import uuid

from bit_share.peer import Peer

from .repository import repository


class JobStatus(enum.Enum):
    IDLE = enum.auto()
    FETCHING_METADATA = enum.auto()
    DOWNLOADING = enum.auto()
    COMPLETED = enum.auto()


class Job:
    def __init__(self, hash: str, destination: Path):
        self.id = str(uuid.uuid4())
        self.hash = hash
        self.status = JobStatus.IDLE
        self.destination = destination

    def download_from_peer(self, peer: Peer, file_index: int):
        data = peer.request_file(file_index)

        file_path = self.destination / peer.package.filelist[file_index][0]
        file_path.parent.mkdir(parents=True, exist_ok=True)
        open(file_path, "wb").write(data)

    def start(self):
        self.status = JobStatus.FETCHING_METADATA
        package = repository.find_package(self.hash)
        assert package is not None, "Package not found in repository"
        peers = repository.find_peers(self.hash)
        for i in range(len(package.filelist)):
            for peer in peers:
                if peer.check_file(i):
                    file = package.filelist[i][0]
                    print(f"[TRANSFER/LOG] downloading file {file} (index {i}) of package {package.name} from peer {peer.ip}")
                    self.download_from_peer(peer, i)
                    break
                else:
                    print(f"[TRANSFER/LOG] peer {peer.ip} does not have file index {i} of package {package.name}")
class Downloader:
    jobs: dict[str, Job]

    def __init__(self):
        self.jobs = {}

    def add_job(self, hash: str, destination: Path) -> str:
        job = Job(hash, destination)
        self.jobs[job.id] = job
        return job
        