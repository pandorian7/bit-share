import enum
from pathlib import Path
import threading
import uuid

from bit_share.peer import Peer

from .repository import repository


class JobStatus(enum.Enum):
    IDLE = enum.auto()
    FETCHING_METADATA = enum.auto()
    DOWNLOADING = enum.auto()
    COMPLETED = enum.auto()
    COMPLETED_WITH_SKIPS = enum.auto()
    FAILED = enum.auto()


class Job:
    def __init__(self, hash: str, destination: Path):
        self.id = str(uuid.uuid4())
        self.hash = hash
        self.status = JobStatus.IDLE
        self.destination = destination
        self.total_files = 0
        self.completed_files = 0
        self.current_file = ""
        self.current_index = -1
        self.skipped_files: list[str] = []
        self.error: str | None = None
        self._lock = threading.Lock()

    def download_from_peer(self, peer: Peer, file_index: int):
        data = peer.request_file(file_index)

        file_path = self.destination / peer.package.filelist[file_index][0]
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "wb") as file:
            file.write(data)

    def snapshot(self) -> dict[str, object]:
        with self._lock:
            done = self.status in {
                JobStatus.COMPLETED,
                JobStatus.COMPLETED_WITH_SKIPS,
                JobStatus.FAILED,
            }
            return {
                "job_id": self.id,
                "hash": self.hash,
                "status": self.status.name,
                "destination": str(self.destination),
                "total_files": self.total_files,
                "completed_files": self.completed_files,
                "current_file": self.current_file,
                "current_index": self.current_index,
                "skipped_files": list(self.skipped_files),
                "error": self.error,
                "done": done,
            }

    def start(self):
        try:
            with self._lock:
                self.status = JobStatus.FETCHING_METADATA

            package = repository.find_package(self.hash)
            if package is None:
                with self._lock:
                    self.status = JobStatus.FAILED
                    self.error = "Package not found in repository"
                return

            with self._lock:
                self.total_files = len(package.filelist)
                self.status = JobStatus.DOWNLOADING

            peers = repository.find_peers(self.hash) or set()
            for i, entry in enumerate(package.filelist):
                file_name = entry[0]
                with self._lock:
                    self.current_index = i
                    self.current_file = file_name

                downloaded = False
                for peer in peers:
                    if peer.check_file(i):
                        print(f"[TRANSFER/LOG] downloading file {file_name} (index {i}) of package {package.name} from peer {peer.ip}")
                        self.download_from_peer(peer, i)
                        with self._lock:
                            self.completed_files += 1
                        downloaded = True
                        break

                    print(f"[TRANSFER/LOG] peer {peer.ip} does not have file index {i} of package {package.name}")

                if not downloaded:
                    with self._lock:
                        self.skipped_files.append(file_name)
                    print(f"[TRANSFER/WARN] skipping missing file {file_name} (index {i}) of package {package.name}")

            with self._lock:
                if self.skipped_files:
                    self.status = JobStatus.COMPLETED_WITH_SKIPS
                else:
                    self.status = JobStatus.COMPLETED
        except Exception as exc:
            with self._lock:
                self.status = JobStatus.FAILED
                self.error = str(exc)


class Downloader:
    jobs: dict[str, Job]

    def __init__(self):
        self.jobs = {}
        self._lock = threading.Lock()

    def add_job(self, hash: str, destination: Path) -> str:
        job = Job(hash, destination)
        with self._lock:
            self.jobs[job.id] = job

        threading.Thread(target=job.start, name=f"download-job-{job.id}", daemon=True).start()
        return job.id

    def get_job_snapshot(self, job_id: str) -> dict[str, object]:
        with self._lock:
            job = self.jobs.get(job_id)

        if job is None:
            return {
                "job_id": job_id,
                "status": "NOT_FOUND",
                "total_files": 0,
                "completed_files": 0,
                "current_file": "",
                "current_index": -1,
                "skipped_files": [],
                "error": "Job not found",
                "done": True,
                "destination": "",
                "hash": "",
            }

        return job.snapshot()
        