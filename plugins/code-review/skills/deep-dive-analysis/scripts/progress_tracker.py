"""
Progress Tracker Module for Deep Dive Analysis.

Manages analysis_progress.json:
- Load/save progress state
- Update file status
- Query files by phase/status/classification
- Calculate progress statistics
"""

import json
import logging
import sys
from collections import Counter
from contextlib import contextmanager
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Literal, Iterator

__all__ = [
    "FileEntry",
    "PhaseInfo",
    "Metadata",
    "ProgressData",
    "ProgressTracker",
]

logger = logging.getLogger(__name__)


@contextmanager
def file_lock(file_handle) -> Iterator[None]:
    """
    Cross-platform file locking context manager.

    On Windows uses msvcrt, on Unix uses fcntl.
    """
    try:
        if sys.platform == "win32":
            import msvcrt
            msvcrt.locking(file_handle.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(file_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield
    except (IOError, OSError) as e:
        logger.warning(f"Could not acquire file lock: {e}")
        yield  # Proceed without lock if unavailable
    finally:
        try:
            if sys.platform == "win32":
                import msvcrt
                msvcrt.locking(file_handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                fcntl.flock(file_handle.fileno(), fcntl.LOCK_UN)
        except (IOError, OSError):
            pass  # Ignore unlock errors


Status = Literal["pending", "analyzing", "done", "blocked"]
Classification = Literal["critical", "high-complexity", "standard", "utility"]


@dataclass
class FileEntry:
    """Entry for a single file in the progress tracker."""

    path: str
    phase: int
    status: Status = "pending"
    classification: Classification | None = None
    verification_required: bool = False
    verification_done: bool = False
    notes: str = ""
    analyzed_at: str | None = None


@dataclass
class PhaseInfo:
    """Information about a phase."""

    name: str
    progress: str = "0/0"
    status: Literal["pending", "in_progress", "completed"] = "pending"


@dataclass
class Metadata:
    """Progress file metadata."""

    started: str = ""
    last_updated: str = ""
    current_phase: int = 1


@dataclass
class ProgressData:
    """Complete progress data structure."""

    metadata: Metadata = field(default_factory=Metadata)
    phases: dict[str, PhaseInfo] = field(default_factory=dict)
    files: list[FileEntry] = field(default_factory=list)


class ProgressTracker:
    """
    Manages analysis progress state.

    Handles loading, saving, and querying the analysis_progress.json file.
    """

    def __init__(self, progress_file: Path | str = "analysis_progress.json"):
        """
        Initialize the progress tracker.

        Args:
            progress_file: Path to the progress JSON file
        """
        self.progress_file = Path(progress_file)
        self.data: ProgressData | None = None

    def load(self) -> ProgressData:
        """
        Load progress from file.

        Returns:
            ProgressData object

        Raises:
            FileNotFoundError: If progress file doesn't exist
        """
        if not self.progress_file.exists():
            raise FileNotFoundError(
                f"Progress file not found: {self.progress_file}\n"
                "Run DEEP_DIVE_PLAN setup to create analysis_progress.json"
            )

        with open(self.progress_file, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        # Parse metadata
        metadata = Metadata(
            started=raw_data.get("metadata", {}).get("started", ""),
            last_updated=raw_data.get("metadata", {}).get("last_updated", ""),
            current_phase=raw_data.get("metadata", {}).get("current_phase", 1),
        )

        # Parse phases
        phases = {}
        for phase_num, phase_data in raw_data.get("phases", {}).items():
            phases[phase_num] = PhaseInfo(
                name=phase_data.get("name", f"Phase {phase_num}"),
                progress=phase_data.get("progress", "0/0"),
                status=phase_data.get("status", "pending"),
            )

        # Parse files
        files = []
        for file_data in raw_data.get("files", []):
            files.append(
                FileEntry(
                    path=file_data.get("path", ""),
                    phase=file_data.get("phase", 1),
                    status=file_data.get("status", "pending"),
                    classification=file_data.get("classification"),
                    verification_required=file_data.get("verification_required", False),
                    verification_done=file_data.get("verification_done", False),
                    notes=file_data.get("notes", ""),
                    analyzed_at=file_data.get("analyzed_at"),
                )
            )

        self.data = ProgressData(metadata=metadata, phases=phases, files=files)
        return self.data

    def save(self) -> None:
        """Save progress to file with file locking for concurrent access safety."""
        if self.data is None:
            raise ValueError("No data to save. Call load() first.")

        # Update last_updated timestamp
        self.data.metadata.last_updated = datetime.now().isoformat()

        # Update phase progress
        for phase_num in self.data.phases:
            phase_files = [f for f in self.data.files if str(f.phase) == phase_num]
            done_files = [f for f in phase_files if f.status == "done"]
            self.data.phases[phase_num].progress = f"{len(done_files)}/{len(phase_files)}"

            # Update phase status
            if len(done_files) == len(phase_files) and len(phase_files) > 0:
                self.data.phases[phase_num].status = "completed"
            elif len(done_files) > 0:
                self.data.phases[phase_num].status = "in_progress"
            else:
                self.data.phases[phase_num].status = "pending"

        # Convert to dict for JSON
        output = {
            "metadata": asdict(self.data.metadata),
            "phases": {k: asdict(v) for k, v in self.data.phases.items()},
            "files": [asdict(f) for f in self.data.files],
        }

        with open(self.progress_file, "w", encoding="utf-8") as f:
            with file_lock(f):
                json.dump(output, f, indent=2)

    def get_file(self, file_path: str) -> FileEntry | None:
        """
        Get a file entry by path.

        Args:
            file_path: Relative path to the file

        Returns:
            FileEntry or None if not found
        """
        if self.data is None:
            self.load()

        # Normalize path separators
        normalized = file_path.replace("\\", "/")

        for entry in self.data.files:
            if entry.path.replace("\\", "/") == normalized:
                return entry

        return None

    def update_file(
        self,
        file_path: str,
        status: Status | None = None,
        classification: Classification | None = None,
        verification_required: bool | None = None,
        verification_done: bool | None = None,
        notes: str | None = None,
    ) -> FileEntry | None:
        """
        Update a file entry.

        Args:
            file_path: Relative path to the file
            status: New status (optional)
            classification: New classification (optional)
            verification_required: Whether verification is required (optional)
            verification_done: Whether verification is done (optional)
            notes: Additional notes (optional)

        Returns:
            Updated FileEntry or None if not found
        """
        entry = self.get_file(file_path)
        if entry is None:
            return None

        if status is not None:
            entry.status = status
            if status == "done":
                entry.analyzed_at = datetime.now().isoformat()

        if classification is not None:
            entry.classification = classification

        if verification_required is not None:
            entry.verification_required = verification_required

        if verification_done is not None:
            entry.verification_done = verification_done

        if notes is not None:
            entry.notes = notes

        return entry

    def get_files_by_phase(self, phase: int) -> list[FileEntry]:
        """Get all files in a specific phase."""
        if self.data is None:
            self.load()

        return [f for f in self.data.files if f.phase == phase]

    def get_files_by_status(self, status: Status) -> list[FileEntry]:
        """Get all files with a specific status."""
        if self.data is None:
            self.load()

        return [f for f in self.data.files if f.status == status]

    def get_files_by_classification(self, classification: Classification) -> list[FileEntry]:
        """Get all files with a specific classification."""
        if self.data is None:
            self.load()

        return [f for f in self.data.files if f.classification == classification]

    def get_files_needing_verification(self) -> list[FileEntry]:
        """Get all files that need verification but haven't been verified."""
        if self.data is None:
            self.load()

        return [
            f
            for f in self.data.files
            if f.verification_required and not f.verification_done
        ]

    def get_next_pending(self, phase: int | None = None) -> FileEntry | None:
        """
        Get the next pending file to analyze.

        Args:
            phase: Optional phase filter

        Returns:
            Next pending FileEntry or None
        """
        if self.data is None:
            self.load()

        pending = [f for f in self.data.files if f.status == "pending"]

        if phase is not None:
            pending = [f for f in pending if f.phase == phase]

        # Prioritize critical files first
        critical = [f for f in pending if f.classification == "critical"]
        if critical:
            return critical[0]

        # Then high-complexity
        high_complexity = [f for f in pending if f.classification == "high-complexity"]
        if high_complexity:
            return high_complexity[0]

        # Then any pending
        if pending:
            return pending[0]

        return None

    def get_statistics(self) -> dict:
        """
        Get overall progress statistics.

        Uses Counter for efficient single-pass computation.

        Returns:
            Dict with statistics
        """
        if self.data is None:
            self.load()

        total = len(self.data.files)

        # Use Counter for efficient single-pass counting
        status_counts = Counter(f.status for f in self.data.files)
        classification_counts = Counter(f.classification for f in self.data.files)

        # Verification counts
        needs_verification = sum(1 for f in self.data.files if f.verification_required)
        verified = sum(
            1 for f in self.data.files
            if f.verification_required and f.verification_done
        )

        done_count = status_counts.get("done", 0)

        return {
            "total_files": total,
            "status": {
                "done": done_count,
                "analyzing": status_counts.get("analyzing", 0),
                "blocked": status_counts.get("blocked", 0),
                "pending": status_counts.get("pending", 0),
            },
            "classification": {
                "critical": classification_counts.get("critical", 0),
                "high_complexity": classification_counts.get("high-complexity", 0),
                "standard": classification_counts.get("standard", 0),
                "utility": classification_counts.get("utility", 0),
                "unclassified": classification_counts.get(None, 0),
            },
            "verification": {
                "required": needs_verification,
                "completed": verified,
                "pending": needs_verification - verified,
            },
            "progress_percentage": round((done_count / total) * 100, 1) if total > 0 else 0,
            "current_phase": self.data.metadata.current_phase,
        }


if __name__ == "__main__":
    import sys

    # Quick test
    tracker = ProgressTracker()

    try:
        tracker.load()
        stats = tracker.get_statistics()
        print(json.dumps(stats, indent=2))

        if len(sys.argv) > 1:
            file_path = sys.argv[1]
            entry = tracker.get_file(file_path)
            if entry:
                print(f"\nFile: {entry.path}")
                print(f"  Phase: {entry.phase}")
                print(f"  Status: {entry.status}")
                print(f"  Classification: {entry.classification}")
                print(f"  Verification required: {entry.verification_required}")
            else:
                print(f"\nFile not found: {file_path}")

    except FileNotFoundError as e:
        print(f"Error: {e}")
