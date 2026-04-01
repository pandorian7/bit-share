import enum
from pathlib import Path
import uuid

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
    
    def start(self):
        self.status = JobStatus.FETCHING_METADATA
        package = repository.find_package(self.hash)
        assert package is not None, "Package not found in repository"
        peers = repository.find_peers(self.hash)
        for i in range(len(package.filelist)):
            file = package.filelist[i]
            print(file)
            for peer in peers:
                if peer.check_file(i):
                    print(f"Peer {peer.ip} has file {i} of package {package.name}")
                    data = peer.request_file(i)
                    print("data", data)
                    break
                else:
                    print(f"Peer {peer.ip} does not have file {i} of package {package.name}")
class Downloader:
    jobs: dict[str, Job]

    def __init__(self):
        self.jobs = {}

    def add_job(self, hash: str, destination: Path) -> str:
        job = Job(hash, destination)
        self.jobs[job.id] = job
        return job
        