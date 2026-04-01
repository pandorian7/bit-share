import enum
import uuid
from zipfile import Path

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
        print(package)


class Downloader:
    jobs: dict[str, Job]

    def __init__(self):
        self.jobs = {}

    def add_job(self, hash: str, destination: Path) -> str:
        job = Job(hash, destination)
        self.jobs[job.id] = job
        return job
        